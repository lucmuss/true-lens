from __future__ import annotations

import hashlib
import hmac
import logging
import random
import secrets
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.db.models import F
from django.http import HttpRequest
from django.utils import timezone

from .models import ApiGateToken, CaptchaChallenge, IPBan, SecurityEvent

logger = logging.getLogger(__name__)


def extract_client_ip(request: HttpRequest) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "127.0.0.1")


def _digest(code: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{code.upper().strip()}".encode()).hexdigest()


_CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _make_captcha_code(length: int = 5) -> str:
    return "".join(secrets.choice(_CAPTCHA_CHARS) for _ in range(length))


_CAPTCHA_BG = (248, 250, 252)  # slate-50
_CAPTCHA_FG_COLORS = [
    (29, 78, 216, 255),    # blue-700
    (37, 99, 235, 255),    # blue-600
    (30, 64, 175, 255),    # blue-800
    (124, 58, 237, 255),   # violet-600 (matches "Konto erstellen" button)
    (15, 23, 42, 255),     # slate-900
]


def create_captcha_challenge() -> dict[str, str]:
    """Generate an image captcha in brand colors, store PNG bytes in DB, return a URL."""
    import io

    from captcha.image import ImageCaptcha

    code = _make_captcha_code()
    salt = secrets.token_hex(8)

    image_gen = ImageCaptcha(width=240, height=80, font_sizes=(36, 40, 44))
    fg = secrets.choice(_CAPTCHA_FG_COLORS)
    img = image_gen.generate_image(code, bg_color=_CAPTCHA_BG, fg_color=fg)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    challenge = CaptchaChallenge.objects.create(
        code_digest=_digest(code, salt),
        salt=salt,
        image_data=image_bytes,
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    return {
        "captcha_id": challenge.captcha_id.hex,
        "image_url": f"/api/security/captcha/image/{challenge.captcha_id.hex}",
        "question": "Gib den abgebildeten Code ein:",
    }


def verify_captcha_challenge(*, captcha_id: str, answer: str, ip: str, user=None) -> bool:
    try:
        challenge = CaptchaChallenge.objects.get(captcha_id=captcha_id)
    except CaptchaChallenge.DoesNotExist:
        return False

    if challenge.solved_at is not None or challenge.expires_at <= timezone.now():
        return False

    expected = _digest(answer, challenge.salt)
    challenge.attempts = F("attempts") + 1
    challenge.save(update_fields=["attempts"])
    challenge.refresh_from_db(fields=["attempts"])

    if challenge.attempts > challenge.max_attempts:
        register_security_failure(ip=ip, reason="captcha max attempts", user=user)
        return False

    if hmac.compare_digest(expected, challenge.code_digest):
        challenge.solved_at = timezone.now()
        challenge.save(update_fields=["solved_at"])
        SecurityEvent.objects.create(
            event_type=SecurityEvent.EventType.CAPTCHA_SOLVED,
            ip=ip,
            user=user if user and user.is_authenticated else None,
            payload={"captcha_id": captcha_id},
        )
        return True

    SecurityEvent.objects.create(
        event_type=SecurityEvent.EventType.CAPTCHA_FAILED,
        ip=ip,
        user=user if user and getattr(user, "is_authenticated", False) else None,
        payload={"captcha_id": captcha_id},
    )
    register_security_failure(ip=ip, reason="captcha mismatch", user=user)
    return False


def _ua_hash(user_agent: str) -> str:
    return hashlib.sha256((user_agent or "").encode("utf-8")).hexdigest()


def create_js_gate_token(*, ip: str, user_agent: str) -> str:
    now = timezone.now()
    exp = now + timedelta(seconds=max(30, settings.API_JS_GATE_TTL_SECONDS))
    payload = {
        "ip": ip,
        "ua": _ua_hash(user_agent),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "rnd": secrets.token_hex(6),
    }
    signer = signing.TimestampSigner(salt="js-gate")
    token = signer.sign_object(payload)
    ApiGateToken.objects.create(
        token=token,
        ip=ip,
        user_agent_hash=payload["ua"],
        expires_at=exp,
    )
    return token


def validate_js_gate_token(*, token: str, ip: str, user_agent: str) -> bool:
    if not token:
        return False
    signer = signing.TimestampSigner(salt="js-gate")
    try:
        payload = signer.unsign_object(token, max_age=settings.API_JS_GATE_TTL_SECONDS + 5)
    except signing.BadSignature:
        return False

    expected_ua = _ua_hash(user_agent)
    if payload.get("ip") != ip or payload.get("ua") != expected_ua:
        return False

    exists = ApiGateToken.objects.filter(
        token=token,
        ip=ip,
        user_agent_hash=expected_ua,
        expires_at__gt=timezone.now(),
    ).exists()
    if not exists:
        return False

    SecurityEvent.objects.create(
        event_type=SecurityEvent.EventType.API_GATE_PASSED,
        ip=ip,
        payload={"token_prefix": token[:16]},
    )
    return True


def is_ip_banned(ip: str) -> bool:
    return IPBan.objects.filter(ip=ip, banned_until__gt=timezone.now()).exists()


def register_security_failure(*, ip: str, reason: str, user=None) -> None:
    until = timezone.now() + timedelta(minutes=max(5, settings.IP_BAN_MINUTES))
    ban, _ = IPBan.objects.get_or_create(
        ip=ip,
        defaults={"reason": reason, "strike_count": 1, "banned_until": until},
    )
    if ban.strike_count >= settings.IP_BAN_THRESHOLD:
        ban.reason = reason
        ban.banned_until = until
        ban.strike_count = ban.strike_count + 1
        ban.save(update_fields=["reason", "banned_until", "strike_count", "updated_at"])
        SecurityEvent.objects.create(
            event_type=SecurityEvent.EventType.IP_BANNED,
            ip=ip,
            user=user if user and getattr(user, "is_authenticated", False) else None,
            payload={"reason": reason, "banned_until": until.isoformat()},
        )
        logger.warning("ip_banned ip=%s reason=%s strikes=%d", ip, reason, ban.strike_count)
    else:
        ban.reason = reason
        ban.strike_count = ban.strike_count + 1
        ban.save(update_fields=["reason", "strike_count", "updated_at"])
        logger.info("security_strike ip=%s reason=%s strikes=%d", ip, reason, ban.strike_count)


def create_captcha_inline(request: HttpRequest) -> dict[str, str]:
    data = create_captcha_challenge()
    request.session["inline_captcha_id"] = data["captcha_id"]
    return data


def verify_captcha_inline(request: HttpRequest, captcha_id: str, answer: str) -> bool:
    expected_id = request.session.get("inline_captcha_id", "")
    if expected_id != captcha_id:
        return False
    return verify_captcha_challenge(
        captcha_id=captcha_id,
        answer=answer,
        ip=extract_client_ip(request),
        user=request.user,
    )

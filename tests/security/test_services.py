from __future__ import annotations

from datetime import timedelta

import pytest
from django.test import RequestFactory, override_settings
from django.utils import timezone

from apps.security.models import ApiGateToken, IPBan, SecurityEvent
from apps.security.services import (
    create_captcha_challenge,
    create_captcha_inline,
    create_js_gate_token,
    is_ip_banned,
    register_security_failure,
    validate_js_gate_token,
    verify_captcha_challenge,
    verify_captcha_inline,
)


@pytest.mark.django_db
def test_create_captcha_challenge_persists_row():
    data = create_captcha_challenge()
    assert "captcha_id" in data
    assert data["image_b64"].startswith("data:image/png;base64,")


@pytest.mark.django_db
def test_verify_captcha_challenge_success(captcha_challenge_factory):
    challenge = captcha_challenge_factory(code="XYZ123")

    ok = verify_captcha_challenge(captcha_id=challenge.captcha_id.hex, answer="XYZ123", ip="127.0.0.1")

    assert ok is True
    solved = challenge.__class__.objects.get(id=challenge.id)
    assert solved.solved_at is not None
    assert SecurityEvent.objects.filter(event_type=SecurityEvent.EventType.CAPTCHA_SOLVED).exists()


@pytest.mark.django_db
def test_verify_captcha_challenge_failure(captcha_challenge_factory):
    challenge = captcha_challenge_factory(code="XYZ123")

    ok = verify_captcha_challenge(captcha_id=challenge.captcha_id.hex, answer="BAD000", ip="127.0.0.1")

    assert ok is False
    refreshed = challenge.__class__.objects.get(id=challenge.id)
    assert refreshed.attempts == 1
    assert SecurityEvent.objects.filter(event_type=SecurityEvent.EventType.CAPTCHA_FAILED).exists()


@pytest.mark.django_db
def test_create_and_validate_js_gate_token_success():
    token = create_js_gate_token(ip="127.0.0.1", user_agent="pytest")

    assert validate_js_gate_token(token=token, ip="127.0.0.1", user_agent="pytest") is True


@pytest.mark.django_db
def test_validate_js_gate_token_rejects_ip_or_ua_mismatch():
    token = create_js_gate_token(ip="127.0.0.1", user_agent="pytest")

    assert validate_js_gate_token(token=token, ip="127.0.0.2", user_agent="pytest") is False
    assert validate_js_gate_token(token=token, ip="127.0.0.1", user_agent="other") is False


@pytest.mark.django_db
def test_validate_js_gate_token_rejects_expired_db_row():
    token = create_js_gate_token(ip="127.0.0.1", user_agent="pytest")
    ApiGateToken.objects.filter(token=token).update(expires_at=timezone.now() - timedelta(seconds=1))

    assert validate_js_gate_token(token=token, ip="127.0.0.1", user_agent="pytest") is False


@pytest.mark.django_db
def test_is_ip_banned_true_for_active_ban(ip_ban_factory):
    ip_ban_factory(ip="127.0.0.3", banned_until=timezone.now() + timedelta(minutes=10))
    assert is_ip_banned("127.0.0.3") is True


@pytest.mark.django_db
@override_settings(IP_BAN_THRESHOLD=2, IP_BAN_MINUTES=10)
def test_register_security_failure_escalates_to_ban():
    register_security_failure(ip="127.0.0.9", reason="bad-1")
    register_security_failure(ip="127.0.0.9", reason="bad-2")

    ban = IPBan.objects.get(ip="127.0.0.9")
    assert ban.strike_count >= 2
    assert ban.banned_until > timezone.now()


@pytest.mark.django_db
def test_inline_captcha_session_flow(captcha_challenge_factory, monkeypatch):
    rf = RequestFactory()
    request = rf.get("/")
    request.session = {}
    request.user = None

    challenge = captcha_challenge_factory(code="HELLO1")
    monkeypatch.setattr(
        "apps.security.services.create_captcha_challenge",
        lambda: {"captcha_id": challenge.captcha_id.hex, "image_b64": "data:image/png;base64,abc"},
    )

    data = create_captcha_inline(request)
    assert request.session["inline_captcha_id"] == data["captcha_id"]

    assert verify_captcha_inline(request, data["captcha_id"], "HELLO1") is True


@pytest.mark.django_db
def test_inline_captcha_rejects_session_mismatch(captcha_challenge_factory):
    rf = RequestFactory()
    request = rf.get("/")
    request.session = {"inline_captcha_id": "expected"}
    request.user = None

    challenge = captcha_challenge_factory(code="HELLO1")

    assert verify_captcha_inline(request, challenge.captcha_id.hex, "HELLO1") is False

from __future__ import annotations

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import create_captcha_challenge, create_js_gate_token, extract_client_ip, verify_captcha_challenge


def _load_body(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


@csrf_exempt
@require_POST
def captcha_start(request):
    data = create_captcha_challenge()
    return JsonResponse({"ok": True, **data})


@csrf_exempt
@require_POST
def captcha_verify(request):
    payload = _load_body(request)
    captcha_id = (payload.get("captcha_id") or "").strip()
    code = (payload.get("code") or "").strip()
    if not captcha_id or not code:
        return JsonResponse({"ok": False, "error": "captcha_id and code are required"}, status=400)

    ip = extract_client_ip(request)
    solved = verify_captcha_challenge(captcha_id=captcha_id, answer=code, ip=ip, user=request.user)
    if not solved:
        return JsonResponse({"ok": False, "error": "Captcha verification failed"}, status=400)

    token = create_js_gate_token(ip=ip, user_agent=request.META.get("HTTP_USER_AGENT", ""))
    return JsonResponse({"ok": True, "js_gate_token": token})

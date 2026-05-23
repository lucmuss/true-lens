from __future__ import annotations

from django.http import JsonResponse

from .services import extract_client_ip, is_ip_banned, validate_js_gate_token


class RequestFingerprintMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.client_ip = extract_client_ip(request)
        request.client_ua = request.META.get("HTTP_USER_AGENT", "")
        return self.get_response(request)


class ApiGateMiddleware:
    ALLOWED_PATH_PREFIXES = (
        "/api/security/captcha/start",
        "/api/security/captcha/verify",
        "/api/security/captcha/image/",
        "/api/credits/webhook/stripe",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        ip = getattr(request, "client_ip", "127.0.0.1")

        if path.startswith("/api/") and not path.startswith(self.ALLOWED_PATH_PREFIXES):
            if is_ip_banned(ip):
                return JsonResponse({"ok": False, "error": "IP temporarily banned"}, status=403)
            # Authenticated users are already verified by Django session — skip gate check.
            user = getattr(request, "user", None)
            if not (user and user.is_authenticated):
                token = request.headers.get("X-JS-Gate", "")
                ua = getattr(request, "client_ua", "")
                if not validate_js_gate_token(token=token, ip=ip, user_agent=ua):
                    return JsonResponse({"ok": False, "error": "Missing or invalid JS gate token"}, status=403)

        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-eval' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self';"
        )
        return response

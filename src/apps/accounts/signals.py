from __future__ import annotations

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from apps.security.services import extract_client_ip

from .services import send_login_alert


@receiver(user_logged_in)
def login_alert_handler(sender, request, user, **kwargs):  # noqa: ANN001
    if request is None:
        return
    ip = extract_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    send_login_alert(user=user, ip=ip, user_agent=user_agent, app_public_url=settings.APP_PUBLIC_URL)

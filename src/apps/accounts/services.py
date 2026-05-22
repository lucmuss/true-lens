from __future__ import annotations

from django.urls import reverse
from django.utils import timezone

from .emails import send_templated_email


def send_login_alert(*, user, ip: str, user_agent: str, app_public_url: str) -> None:
    if not user.notify_on_security:
        return

    context = {
        "user": user,
        "ip": ip,
        "user_agent": user_agent or "unknown",
        "occurred_at": timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M"),
        "dashboard_url": f"{app_public_url}{reverse('dashboard')}",
        "password_url": f"{app_public_url}{reverse('account_change_password')}",
    }
    send_templated_email(
        to=[user.email],
        subject="Sicherheitsmeldung: erfolgreicher Login",
        text_template="emails/login_alert.txt",
        html_template="emails/login_alert.html",
        context=context,
    )

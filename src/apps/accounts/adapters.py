from __future__ import annotations

import secrets
from datetime import timedelta

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .models import RecruiterSecurityVerification


class RecruiterAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        # Keep allauth internal mail behavior, while custom security challenge is sent separately.
        return super().send_mail(template_prefix, email, context)

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.display_name = user.display_name or (user.email.split("@", 1)[0] if user.email else "")
        if commit:
            user.save()
            self._send_security_challenge(user, request)
        return user

    def _send_security_challenge(self, user, request) -> None:
        code = f"{secrets.randbelow(10**6):06d}"
        challenge = RecruiterSecurityVerification.objects.create(
            recruiter=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=20),
        )
        verify_url = request.build_absolute_uri(
            reverse("account_security_verify", kwargs={"token": challenge.token.hex})
        )
        body = render_to_string(
            "emails/security_verification.txt",
            {
                "code": code,
                "verify_url": verify_url,
                "expires_minutes": 20,
                "project_name": settings.PROJECT_NAME,
            },
        )
        send_mail(
            subject=f"{settings.PROJECT_NAME}: Sicherheitscode",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

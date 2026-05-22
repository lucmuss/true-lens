from __future__ import annotations

from allauth.account.adapter import DefaultAccountAdapter


class RecruiterAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        return super().send_mail(template_prefix, email, context)

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.display_name = user.display_name or (user.email.split("@", 1)[0] if user.email else "")
        if commit:
            user.save()
        return user

    def confirm_email(self, request, email_address):
        """Mark recruiter as verified once allauth confirms the email address."""
        super().confirm_email(request, email_address)
        user = email_address.user
        if not user.is_verified_recruiter:
            user.is_verified_recruiter = True
            user.save(update_fields=["is_verified_recruiter"])

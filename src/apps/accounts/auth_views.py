"""Custom allauth login/signup/password-reset views that require a solved captcha gate token."""
from __future__ import annotations

from allauth.account.views import LoginView as AllauthLoginView
from allauth.account.views import PasswordResetView as AllauthPasswordResetView
from allauth.account.views import SignupView as AllauthSignupView

from apps.candidates.models import Candidate, CandidateAttributeVote
from apps.security.services import extract_client_ip, validate_js_gate_token


def _stats() -> dict:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return {
        "candidate_count": Candidate.objects.count(),
        "recruiter_count": User.objects.filter(is_active=True, is_verified_recruiter=True).count(),
        "total_votes": CandidateAttributeVote.objects.count(),
    }


class LoginWithCaptchaView(AllauthLoginView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_stats())
        return ctx

    def form_valid(self, form):
        token = self.request.POST.get("captcha_token", "").strip()
        ip = extract_client_ip(self.request)
        ua = self.request.META.get("HTTP_USER_AGENT", "")
        if not validate_js_gate_token(token=token, ip=ip, user_agent=ua):
            form.add_error(None, "Bitte löse zuerst das Sicherheits-Captcha.")
            return self.form_invalid(form)
        return super().form_valid(form)


class SignupWithCaptchaView(AllauthSignupView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_stats())
        return ctx

    def form_valid(self, form):
        token = self.request.POST.get("captcha_token", "").strip()
        ip = extract_client_ip(self.request)
        ua = self.request.META.get("HTTP_USER_AGENT", "")
        if not validate_js_gate_token(token=token, ip=ip, user_agent=ua):
            form.add_error(None, "Bitte löse zuerst das Sicherheits-Captcha.")
            return self.form_invalid(form)
        return super().form_valid(form)


class PasswordResetWithStatsView(AllauthPasswordResetView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_stats())
        return ctx

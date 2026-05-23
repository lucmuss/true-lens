"""URL overrides to intercept allauth login/signup/password-reset with captcha validation."""
from django.urls import path

from .auth_views import LoginWithCaptchaView, PasswordResetWithStatsView, SignupWithCaptchaView

urlpatterns = [
    path("login/", LoginWithCaptchaView.as_view(), name="account_login"),
    path("signup/", SignupWithCaptchaView.as_view(), name="account_signup"),
    path("password/reset/", PasswordResetWithStatsView.as_view(), name="account_reset_password"),
]

"""URL overrides to intercept allauth login/signup with captcha validation."""
from django.urls import path

from .auth_views import LoginWithCaptchaView, SignupWithCaptchaView

urlpatterns = [
    path("login/", LoginWithCaptchaView.as_view(), name="account_login"),
    path("signup/", SignupWithCaptchaView.as_view(), name="account_signup"),
]

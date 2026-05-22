from django.urls import path

from . import api_views

urlpatterns = [
    path("security/captcha/start", api_views.captcha_start, name="api_captcha_start"),
    path("security/captcha/verify", api_views.captcha_verify, name="api_captcha_verify"),
]

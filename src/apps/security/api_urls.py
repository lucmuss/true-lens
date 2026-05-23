from django.urls import path

from . import api_views

urlpatterns = [
    path("security/captcha/start", api_views.captcha_start, name="api_captcha_start"),
    path("security/captcha/verify", api_views.captcha_verify, name="api_captcha_verify"),
    path("security/captcha/image/<str:captcha_id>", api_views.captcha_image, name="api_captcha_image"),
    path("security/gate/check", api_views.gate_check, name="api_gate_check"),
]

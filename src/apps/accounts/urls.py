from django.urls import path

from . import views

urlpatterns = [
    path("security-verify/<str:token>/", views.security_verify, name="account_security_verify"),
    path("settings/", views.recruiter_settings, name="recruiter_settings"),
    path("delete/", views.delete_recruiter_profile, name="recruiter_delete"),
]

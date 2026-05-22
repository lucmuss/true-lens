from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profiles/<int:candidate_id>/", views.profile_page, name="candidate_profile"),
]

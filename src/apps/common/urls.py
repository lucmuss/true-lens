from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("votes/", views.vote_history, name="vote_history"),
    path("billing/", views.billing, name="billing"),
    path("admin-overview/", views.admin_dashboard, name="admin_dashboard"),
    path("profiles/<int:candidate_id>/", views.profile_page, name="candidate_profile"),
]

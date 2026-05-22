from django.urls import path

from . import api_views

urlpatterns = [
    path("recruiters/contact-request", api_views.create_contact_request, name="api_contact_request_create"),
    path(
        "recruiters/contact-request/<int:relay_id>/accept",
        api_views.accept_contact_request,
        name="api_contact_request_accept",
    ),
    path(
        "recruiters/contact-request/<int:relay_id>/reject",
        api_views.reject_contact_request,
        name="api_contact_request_reject",
    ),
]

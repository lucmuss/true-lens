from django.urls import path

from . import api_views

urlpatterns = [
    path("internal/heartbeat", api_views.heartbeat, name="api_internal_heartbeat"),
    path("internal/election", api_views.election, name="api_internal_election"),
    path("internal/replication/push", api_views.repl_push, name="api_internal_repl_push"),
    path("internal/replication/ack", api_views.repl_ack, name="api_internal_repl_ack"),
]

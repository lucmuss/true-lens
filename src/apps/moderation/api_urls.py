from django.urls import path

from . import api_views

urlpatterns = [
    path("moderation/queue", api_views.queue_list, name="api_moderation_queue"),
    path("moderation/queue/<int:item_id>/approve", api_views.queue_approve, name="api_moderation_queue_approve"),
    path("moderation/queue/<int:item_id>/reject", api_views.queue_reject, name="api_moderation_queue_reject"),
]

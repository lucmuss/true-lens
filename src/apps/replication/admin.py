from django.contrib import admin

from .models import NodeInstance, ReplicationEvent, ReplicationJob


@admin.register(NodeInstance)
class NodeInstanceAdmin(admin.ModelAdmin):
    list_display = ("name", "base_url", "role", "status", "is_approved", "heartbeat_at")
    list_filter = ("role", "status", "is_approved")
    search_fields = ("name", "base_url")


@admin.register(ReplicationJob)
class ReplicationJobAdmin(admin.ModelAdmin):
    list_display = ("event_id", "target_node", "status", "attempts", "created_at")
    list_filter = ("status",)
    search_fields = ("event_id", "target_node__name", "target_node__base_url")


@admin.register(ReplicationEvent)
class ReplicationEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "source_node_id", "acknowledged_at")
    search_fields = ("event_id", "source_node_id")

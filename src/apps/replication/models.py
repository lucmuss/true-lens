from __future__ import annotations

import uuid

from django.db import models


class NodeInstance(models.Model):
    class Role(models.TextChoices):
        COORDINATOR = "coordinator", "Coordinator"
        BACKUP_COORDINATOR = "backup", "Backup Coordinator"
        REPLICA = "replica", "Replica"

    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        DEGRADED = "degraded", "Degraded"

    node_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=120)
    base_url = models.URLField(unique=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.REPLICA)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OFFLINE)
    api_token_hint = models.CharField(max_length=32, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "node_instance"
        indexes = [models.Index(fields=["role", "status"]), models.Index(fields=["heartbeat_at"])]


class ReplicationJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        ACKED = "acked", "Acked"
        FAILED = "failed", "Failed"

    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    target_node = models.ForeignKey(NodeInstance, on_delete=models.CASCADE, related_name="incoming_jobs")
    payload_ciphertext = models.TextField()
    payload_checksum = models.CharField(max_length=128)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    error_message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "replication_job"
        indexes = [models.Index(fields=["status", "created_at"])]


class ReplicationEvent(models.Model):
    event_id = models.UUIDField(unique=True)
    source_node_id = models.UUIDField()
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "replication_event"
        indexes = [models.Index(fields=["source_node_id", "acknowledged_at"])]

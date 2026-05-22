from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import NodeInstance, ReplicationEvent, ReplicationJob


class InternalAuthError(RuntimeError):
    pass


def _secret() -> bytes:
    return settings.REPLICATION_SHARED_SECRET.encode("utf-8")


def sign_payload(payload: dict, *, timestamp: int) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    msg = f"{timestamp}.".encode() + body
    digest = hmac.new(_secret(), msg, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8")


def verify_signature(payload: dict, *, timestamp: int, signature: str) -> bool:
    now_ts = int(timezone.now().timestamp())
    if abs(now_ts - int(timestamp)) > 300:
        return False
    expected = sign_payload(payload, timestamp=timestamp)
    return hmac.compare_digest(expected, signature)


def encrypt_payload(payload: dict) -> tuple[str, str]:
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    # Placeholder symmetric envelope: base64 + HMAC checksum.
    ciphertext = base64.urlsafe_b64encode(data).decode("utf-8")
    checksum = hmac.new(_secret(), data, hashlib.sha256).hexdigest()
    return ciphertext, checksum


def decrypt_payload(ciphertext: str, checksum: str) -> dict:
    data = base64.urlsafe_b64decode(ciphertext.encode("utf-8"))
    expected = hmac.new(_secret(), data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, checksum):
        raise InternalAuthError("payload checksum mismatch")
    return json.loads(data.decode("utf-8"))


def heartbeat_node(*, node_name: str, base_url: str) -> NodeInstance:
    node, _ = NodeInstance.objects.get_or_create(
        base_url=base_url,
        defaults={"name": node_name, "status": NodeInstance.Status.ONLINE},
    )
    node.name = node_name
    node.status = NodeInstance.Status.ONLINE
    node.heartbeat_at = timezone.now()
    node.save(update_fields=["name", "status", "heartbeat_at", "updated_at"])
    return node


def evaluate_coordinator_failover() -> NodeInstance | None:
    threshold = timezone.now() - timedelta(seconds=settings.COORDINATOR_DOWN_THRESHOLD_SECONDS)
    coordinator = NodeInstance.objects.filter(role=NodeInstance.Role.COORDINATOR, is_approved=True).first()
    if coordinator and coordinator.heartbeat_at and coordinator.heartbeat_at > threshold:
        return coordinator

    backup = NodeInstance.objects.filter(role=NodeInstance.Role.BACKUP_COORDINATOR, is_approved=True).first()
    if backup:
        backup.role = NodeInstance.Role.COORDINATOR
        backup.status = NodeInstance.Status.ONLINE
        backup.save(update_fields=["role", "status", "updated_at"])
        return backup
    return None


def enqueue_replication(*, target_node: NodeInstance, payload: dict) -> ReplicationJob:
    ciphertext, checksum = encrypt_payload(payload)
    return ReplicationJob.objects.create(
        target_node=target_node,
        payload_ciphertext=ciphertext,
        payload_checksum=checksum,
    )


def acknowledge_event(*, event_id: str, source_node_id: str) -> None:
    ReplicationEvent.objects.get_or_create(event_id=event_id, defaults={"source_node_id": source_node_id})

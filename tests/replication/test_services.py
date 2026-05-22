from __future__ import annotations

import base64
import json

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.replication.models import NodeInstance, ReplicationEvent
from apps.replication.services import (
    InternalAuthError,
    acknowledge_event,
    decrypt_payload,
    encrypt_payload,
    enqueue_replication,
    evaluate_coordinator_failover,
    heartbeat_node,
    sign_payload,
    verify_signature,
)


@pytest.mark.django_db
@override_settings(REPLICATION_SHARED_SECRET="secret", COORDINATOR_DOWN_THRESHOLD_SECONDS=3600)
def test_sign_and_verify_payload_success():
    payload = {"event": "x", "id": 1}
    ts = int(timezone.now().timestamp())
    sig = sign_payload(payload, timestamp=ts)

    assert verify_signature(payload, timestamp=ts, signature=sig) is True


@pytest.mark.django_db
@override_settings(REPLICATION_SHARED_SECRET="secret")
def test_verify_signature_rejects_stale_timestamp():
    payload = {"event": "x"}
    ts = int(timezone.now().timestamp()) - 1000
    sig = sign_payload(payload, timestamp=ts)

    assert verify_signature(payload, timestamp=ts, signature=sig) is False


@pytest.mark.django_db
@override_settings(REPLICATION_SHARED_SECRET="secret")
def test_encrypt_decrypt_roundtrip():
    payload = {"a": 1, "b": "two"}
    ciphertext, checksum = encrypt_payload(payload)

    restored = decrypt_payload(ciphertext, checksum)
    assert restored == payload


@pytest.mark.django_db
@override_settings(REPLICATION_SHARED_SECRET="secret")
def test_decrypt_payload_rejects_bad_checksum():
    payload = {"a": 1}
    ciphertext, checksum = encrypt_payload(payload)

    with pytest.raises(InternalAuthError):
        decrypt_payload(ciphertext, checksum + "x")


@pytest.mark.django_db
def test_heartbeat_node_creates_or_updates():
    node = heartbeat_node(node_name="n1", base_url="https://n1.example.com")
    assert node.status == NodeInstance.Status.ONLINE

    node2 = heartbeat_node(node_name="n1-updated", base_url="https://n1.example.com")
    assert node2.id == node.id
    assert node2.name == "n1-updated"


@pytest.mark.django_db
@override_settings(COORDINATOR_DOWN_THRESHOLD_SECONDS=3600)
def test_evaluate_coordinator_returns_healthy_existing(node_instance_factory):
    coordinator = node_instance_factory(
        role=NodeInstance.Role.COORDINATOR,
        heartbeat_at=timezone.now(),
        is_approved=True,
    )
    result = evaluate_coordinator_failover()
    assert result.id == coordinator.id


@pytest.mark.django_db
def test_evaluate_coordinator_promotes_backup(node_instance_factory):
    node_instance_factory(
        role=NodeInstance.Role.COORDINATOR,
        heartbeat_at=timezone.now() - timezone.timedelta(days=2),
        is_approved=True,
    )
    backup = node_instance_factory(
        role=NodeInstance.Role.BACKUP_COORDINATOR,
        heartbeat_at=timezone.now(),
        is_approved=True,
    )

    result = evaluate_coordinator_failover()

    backup.refresh_from_db()
    assert result.id == backup.id
    assert backup.role == NodeInstance.Role.COORDINATOR


@pytest.mark.django_db
def test_enqueue_replication_creates_pending_job(node_instance_factory):
    target = node_instance_factory()
    job = enqueue_replication(target_node=target, payload={"foo": "bar"})

    assert job.status == job.Status.PENDING
    assert job.target_node_id == target.id


@pytest.mark.django_db
def test_acknowledge_event_is_idempotent():
    event_id = "1f2f3f4f-1234-4bcd-9cde-123456789012"
    source_a = "9d86f8cc-4735-4f1f-b669-a6b5f33fe243"
    source_b = "d1bf55e4-df88-4279-90bf-27444f57a3cf"
    acknowledge_event(event_id=event_id, source_node_id=source_a)
    acknowledge_event(event_id=event_id, source_node_id=source_b)

    events = ReplicationEvent.objects.filter(event_id=event_id)
    assert events.count() == 1
    assert str(events.first().source_node_id) == source_a

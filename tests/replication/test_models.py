from __future__ import annotations

import pytest

from apps.replication.models import NodeInstance, ReplicationJob


@pytest.mark.django_db
def test_node_instance_defaults(node_instance_factory):
    node = node_instance_factory(role=NodeInstance.Role.REPLICA)
    assert node.status == NodeInstance.Status.ONLINE
    assert node.node_id is not None


@pytest.mark.django_db
def test_replication_job_defaults(node_instance_factory):
    node = node_instance_factory()
    job = ReplicationJob.objects.create(
        target_node=node,
        payload_ciphertext="cipher",
        payload_checksum="checksum",
    )
    assert job.status == ReplicationJob.Status.PENDING
    assert job.attempts == 0


@pytest.mark.django_db
def test_replication_event_id_unique(node_instance_factory):
    node = node_instance_factory()
    job = ReplicationJob.objects.create(
        target_node=node,
        payload_ciphertext="cipher2",
        payload_checksum="checksum2",
    )
    assert job.event_id is not None

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.replication.models import NodeInstance
from apps.replication.services import evaluate_coordinator_failover


@pytest.mark.django_db
def test_failover_with_two_nodes_down_promotes_backup_coordinator(settings):
    settings.COORDINATOR_DOWN_THRESHOLD_SECONDS = 3600

    NodeInstance.objects.create(
        name="primary",
        base_url="https://primary.example",
        role=NodeInstance.Role.COORDINATOR,
        status=NodeInstance.Status.OFFLINE,
        is_approved=True,
        heartbeat_at=timezone.now() - timedelta(hours=3),
    )
    backup = NodeInstance.objects.create(
        name="backup",
        base_url="https://backup.example",
        role=NodeInstance.Role.BACKUP_COORDINATOR,
        status=NodeInstance.Status.ONLINE,
        is_approved=True,
        heartbeat_at=timezone.now(),
    )
    NodeInstance.objects.create(
        name="replica",
        base_url="https://replica.example",
        role=NodeInstance.Role.REPLICA,
        status=NodeInstance.Status.OFFLINE,
        is_approved=True,
        heartbeat_at=timezone.now() - timedelta(hours=5),
    )

    active = evaluate_coordinator_failover()
    assert active is not None
    assert active.id == backup.id
    backup.refresh_from_db()
    assert backup.role == NodeInstance.Role.COORDINATOR

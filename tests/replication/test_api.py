from __future__ import annotations

import json

import pytest
from django.utils import timezone

from apps.replication.models import ReplicationEvent
from apps.replication.services import sign_payload


def _signed_headers(payload: dict) -> dict[str, str]:
    ts = int(timezone.now().timestamp())
    sig = sign_payload(payload, timestamp=ts)
    return {
        "HTTP_X_INTERNAL_TIMESTAMP": str(ts),
        "HTTP_X_INTERNAL_SIGNATURE": sig,
    }


@pytest.fixture(autouse=True)
def _bypass_js_gate(monkeypatch):
    monkeypatch.setattr("apps.security.middleware.validate_js_gate_token", lambda **kwargs: True)
    monkeypatch.setattr("apps.security.middleware.is_ip_banned", lambda _ip: False)


@pytest.mark.django_db
def test_internal_heartbeat_rejects_invalid_signature(client):
    payload = {"name": "node-a", "base_url": "https://node-a.example.com"}

    response = client.post(
        "/api/internal/heartbeat",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_INTERNAL_TIMESTAMP="1",
        HTTP_X_INTERNAL_SIGNATURE="bad",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_internal_heartbeat_success(client):
    payload = {"name": "node-a", "base_url": "https://node-a.example.com"}
    headers = _signed_headers(payload)

    response = client.post("/api/internal/heartbeat", data=json.dumps(payload), content_type="application/json", **headers)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["node_id"]


@pytest.mark.django_db
def test_internal_election_success(client):
    payload = {}
    headers = _signed_headers(payload)

    response = client.post("/api/internal/election", data=json.dumps(payload), content_type="application/json", **headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_internal_repl_push_404_for_unknown_target(client):
    payload = {"target_base_url": "https://unknown-node.example.com", "event": {"kind": "sync"}}
    headers = _signed_headers(payload)

    response = client.post("/api/internal/replication/push", data=json.dumps(payload), content_type="application/json", **headers)
    assert response.status_code == 404


@pytest.mark.django_db
def test_internal_repl_push_success(client, node_instance_factory):
    target = node_instance_factory(base_url="https://known-node.example.com", is_approved=True)
    payload = {"target_base_url": target.base_url, "event": {"kind": "sync", "id": 1}}
    headers = _signed_headers(payload)

    response = client.post("/api/internal/replication/push", data=json.dumps(payload), content_type="application/json", **headers)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["status"] == "pending"


@pytest.mark.django_db
def test_internal_repl_ack_requires_fields(client):
    payload = {}
    headers = _signed_headers(payload)

    response = client.post("/api/internal/replication/ack", data=json.dumps(payload), content_type="application/json", **headers)
    assert response.status_code == 400


@pytest.mark.django_db
def test_internal_repl_ack_success(client):
    payload = {
        "event_id": "b292f8ec-d2b9-4f2d-bf5d-2d3248085679",
        "source_node_id": "d96f34f2-36f1-4132-bf6a-f80512089afd",
    }
    headers = _signed_headers(payload)

    response = client.post("/api/internal/replication/ack", data=json.dumps(payload), content_type="application/json", **headers)

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert ReplicationEvent.objects.filter(event_id=payload["event_id"]).exists()

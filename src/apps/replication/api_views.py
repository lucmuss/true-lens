from __future__ import annotations

import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import NodeInstance
from .services import (
    acknowledge_event,
    enqueue_replication,
    evaluate_coordinator_failover,
    heartbeat_node,
    verify_signature,
)


def _body(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _internal_auth(request, payload: dict) -> bool:
    signature = request.headers.get("X-Internal-Signature", "")
    timestamp_raw = request.headers.get("X-Internal-Timestamp", "0")
    try:
        timestamp = int(timestamp_raw)
    except ValueError:
        return False
    return verify_signature(payload, timestamp=timestamp, signature=signature)


@require_POST
def heartbeat(request):
    payload = _body(request)
    if not _internal_auth(request, payload):
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    node = heartbeat_node(node_name=payload.get("name", "unknown"), base_url=payload.get("base_url", ""))
    coordinator = evaluate_coordinator_failover()
    return JsonResponse(
        {
            "ok": True,
            "node_id": str(node.node_id),
            "active_coordinator": str(coordinator.node_id) if coordinator else None,
        }
    )


@require_POST
def election(request):
    payload = _body(request)
    if not _internal_auth(request, payload):
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)
    coordinator = evaluate_coordinator_failover()
    return JsonResponse({"ok": True, "coordinator": str(coordinator.node_id) if coordinator else None})


@require_POST
def repl_push(request):
    payload = _body(request)
    if not _internal_auth(request, payload):
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)

    target_url = payload.get("target_base_url", "")
    target = NodeInstance.objects.filter(base_url=target_url, is_approved=True).first()
    if target is None:
        return JsonResponse({"ok": False, "error": "target node not found"}, status=404)

    job = enqueue_replication(target_node=target, payload=payload.get("event", {}))
    return JsonResponse({"ok": True, "event_id": str(job.event_id), "status": job.status})


@require_POST
def repl_ack(request):
    payload = _body(request)
    if not _internal_auth(request, payload):
        return JsonResponse({"ok": False, "error": "unauthorized"}, status=403)

    event_id = str(payload.get("event_id", ""))
    source = str(payload.get("source_node_id", ""))
    if not event_id or not source:
        return JsonResponse({"ok": False, "error": "event_id and source_node_id required"}, status=400)

    acknowledge_event(event_id=event_id, source_node_id=source)
    return JsonResponse({"ok": True})

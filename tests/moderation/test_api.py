from __future__ import annotations

import pytest

from apps.moderation.models import DataEnrichmentSubmission


@pytest.mark.django_db
def test_queue_list_requires_staff(client, js_gate_headers, recruiter_factory):
    user = recruiter_factory(is_staff=False)
    client.force_login(user)

    response = client.get("/api/moderation/queue", **js_gate_headers)
    assert response.status_code == 302


@pytest.mark.django_db
def test_queue_list_staff_success(client, js_gate_headers, superuser, candidate_factory, recruiter_factory):
    candidate = candidate_factory()
    recruiter = recruiter_factory()
    DataEnrichmentSubmission.objects.create(candidate=candidate, recruiter=recruiter, payload={"city": "Hamburg"})

    client.force_login(superuser)
    response = client.get("/api/moderation/queue", **js_gate_headers)

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert len(response.json()["items"]) >= 1


@pytest.mark.django_db
def test_queue_approve_404_for_missing_item(client, js_gate_headers, superuser):
    client.force_login(superuser)
    response = client.post("/api/moderation/queue/99999/approve", **js_gate_headers)
    assert response.status_code == 404


@pytest.mark.django_db
def test_queue_approve_updates_candidate_and_status(client, js_gate_headers, superuser, candidate_factory, recruiter_factory):
    candidate = candidate_factory(city="Berlin")
    recruiter = recruiter_factory()
    item = DataEnrichmentSubmission.objects.create(
        candidate=candidate,
        recruiter=recruiter,
        payload={"city": "Hamburg", "secondary_email": "new@example.com", "first_name": "blocked"},
    )

    client.force_login(superuser)
    response = client.post(f"/api/moderation/queue/{item.id}/approve", **js_gate_headers)

    assert response.status_code == 200
    item.refresh_from_db()
    candidate.refresh_from_db()
    assert item.status == DataEnrichmentSubmission.Status.APPROVED
    assert item.reviewed_at is not None
    assert candidate.city == "Hamburg"
    assert candidate.first_name != "blocked"


@pytest.mark.django_db
def test_queue_reject_marks_reviewed(client, js_gate_headers, superuser, candidate_factory, recruiter_factory):
    item = DataEnrichmentSubmission.objects.create(
        candidate=candidate_factory(),
        recruiter=recruiter_factory(),
        payload={"city": "Hamburg"},
    )
    client.force_login(superuser)

    response = client.post(f"/api/moderation/queue/{item.id}/reject", **js_gate_headers)

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.status == DataEnrichmentSubmission.Status.REJECTED
    assert item.reviewed_at is not None


@pytest.mark.django_db
def test_queue_reject_fails_when_already_reviewed(client, js_gate_headers, superuser, candidate_factory, recruiter_factory):
    item = DataEnrichmentSubmission.objects.create(
        candidate=candidate_factory(),
        recruiter=recruiter_factory(),
        payload={"city": "Hamburg"},
        status=DataEnrichmentSubmission.Status.APPROVED,
    )
    client.force_login(superuser)

    response = client.post(f"/api/moderation/queue/{item.id}/reject", **js_gate_headers)
    assert response.status_code == 400

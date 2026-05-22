from __future__ import annotations

import json

import pytest

from apps.accounts.models import RecruiterContactRelay


@pytest.mark.django_db
def test_create_contact_request_requires_login(client, candidate_factory, js_gate_headers):
    candidate = candidate_factory()
    response = client.post(
        "/api/recruiters/contact-request",
        data=json.dumps({"candidate_id": candidate.id, "target_email": "x@example.com"}),
        content_type="application/json",
        **js_gate_headers,
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_create_contact_request_validates_required_fields(client, recruiter_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)

    response = client.post(
        "/api/recruiters/contact-request",
        data=json.dumps({}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_contact_request_rejects_unknown_candidate(client, recruiter_factory, js_gate_headers):
    initiator = recruiter_factory(email="i@example.com")
    target = recruiter_factory(email="t@example.com")
    client.force_login(initiator)

    response = client.post(
        "/api/recruiters/contact-request",
        data=json.dumps({"candidate_id": 777, "target_email": target.email}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_create_contact_request_success(client, recruiter_factory, candidate_factory, js_gate_headers, monkeypatch):
    initiator = recruiter_factory(email="init@example.com")
    target = recruiter_factory(email="target@example.com")
    candidate = candidate_factory()
    client.force_login(initiator)

    monkeypatch.setattr("apps.accounts.api_views.send_mail", lambda **kwargs: None)

    response = client.post(
        "/api/recruiters/contact-request",
        data=json.dumps({"candidate_id": candidate.id, "target_email": target.email, "message": "hi"}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert RecruiterContactRelay.objects.filter(initiator=initiator, target=target, candidate_id=candidate.id).exists()


@pytest.mark.django_db
def test_accept_contact_request_404_for_non_target_user(client, recruiter_factory, js_gate_headers):
    initiator = recruiter_factory(email="init2@example.com")
    target = recruiter_factory(email="target2@example.com")
    other = recruiter_factory(email="other2@example.com")
    relay = RecruiterContactRelay.objects.create(initiator=initiator, target=target, candidate_id=1)
    client.force_login(other)

    response = client.post(f"/api/recruiters/contact-request/{relay.id}/accept", **js_gate_headers)
    assert response.status_code == 404


@pytest.mark.django_db
def test_accept_contact_request_success(client, recruiter_factory, candidate_factory, js_gate_headers, monkeypatch):
    initiator = recruiter_factory(email="init3@example.com")
    target = recruiter_factory(email="target3@example.com")
    candidate = candidate_factory()
    relay = RecruiterContactRelay.objects.create(initiator=initiator, target=target, candidate_id=candidate.id)
    client.force_login(target)

    monkeypatch.setattr("apps.accounts.api_views.send_mail", lambda **kwargs: None)

    response = client.post(f"/api/recruiters/contact-request/{relay.id}/accept", **js_gate_headers)

    assert response.status_code == 200
    relay.refresh_from_db()
    assert relay.status == RecruiterContactRelay.Status.ACCEPTED


@pytest.mark.django_db
def test_reject_contact_request_success(client, recruiter_factory, js_gate_headers):
    initiator = recruiter_factory(email="init4@example.com")
    target = recruiter_factory(email="target4@example.com")
    relay = RecruiterContactRelay.objects.create(initiator=initiator, target=target, candidate_id=1)
    client.force_login(target)

    response = client.post(f"/api/recruiters/contact-request/{relay.id}/reject", **js_gate_headers)

    assert response.status_code == 200
    relay.refresh_from_db()
    assert relay.status == RecruiterContactRelay.Status.REJECTED

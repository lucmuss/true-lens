from __future__ import annotations

import json

import pytest

from apps.candidates.models import CandidateAttributeVote


@pytest.mark.django_db
def test_candidate_vote_requires_authentication(client, candidate_factory, attribute_factory, js_gate_headers):
    candidate = candidate_factory()
    attribute_factory(code=1, slug="reliable", label="Reliable")

    response = client.post(
        f"/api/candidates/{candidate.id}/vote",
        data=json.dumps({"attribute_codes": [1]}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_candidate_vote_rejects_non_integer_codes(client, recruiter_factory, candidate_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)
    candidate = candidate_factory()

    response = client.post(
        f"/api/candidates/{candidate.id}/vote",
        data=json.dumps({"attribute_codes": ["x"]}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_candidate_vote_rejects_duplicate_vote(client, recruiter_factory, candidate_factory, attribute_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)
    candidate = candidate_factory()
    attr = attribute_factory(code=7, slug="smart", label="Smart")

    CandidateAttributeVote.objects.create(candidate=candidate, attribute=attr, recruiter=user)

    response = client.post(
        f"/api/candidates/{candidate.id}/vote",
        data=json.dumps({"attribute_codes": [7]}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_candidate_vote_success(client, recruiter_factory, candidate_factory, attribute_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)
    candidate = candidate_factory()
    attribute_factory(code=8, slug="intro", label="Intro")

    response = client.post(
        f"/api/candidates/{candidate.id}/vote",
        data=json.dumps({"attribute_codes": [8], "anonymous": True}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_candidate_votes_returns_404_for_unknown_candidate(client, js_gate_headers):
    response = client.get("/api/candidates/999999/votes", **js_gate_headers)
    assert response.status_code == 404


@pytest.mark.django_db
def test_candidate_create_requires_auth(client, js_gate_headers):
    response = client.post(
        "/api/candidates/create",
        data=json.dumps({"first_name": "A"}),
        content_type="application/json",
        **js_gate_headers,
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_candidate_create_invalid_payload(client, recruiter_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)

    response = client.post(
        "/api/candidates/create",
        data=json.dumps({"first_name": "Only"}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_candidate_enrichment_requires_auth(client, candidate_factory, js_gate_headers):
    candidate = candidate_factory()

    response = client.post(
        f"/api/candidates/{candidate.id}/enrichment",
        data=json.dumps({"city": "Hamburg"}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_candidate_enrichment_404_for_unknown_candidate(client, recruiter_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)

    response = client.post(
        "/api/candidates/424242/enrichment",
        data=json.dumps({"city": "Hamburg"}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 400
    assert "not found" in response.json()["error"].lower()


@pytest.mark.django_db
def test_candidate_enrichment_rejects_non_editable_only_payload(client, recruiter_factory, candidate_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)
    candidate = candidate_factory()

    response = client.post(
        f"/api/candidates/{candidate.id}/enrichment",
        data=json.dumps({"first_name": "Nope"}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_candidate_enrichment_success(client, recruiter_factory, candidate_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)
    candidate = candidate_factory()

    response = client.post(
        f"/api/candidates/{candidate.id}/enrichment",
        data=json.dumps({"secondary_email": "new@example.com", "city": "Munich"}),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True

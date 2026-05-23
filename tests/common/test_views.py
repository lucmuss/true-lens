from __future__ import annotations

import pytest
from django.urls import reverse

from apps.accounts.models import RecruiterContactRelay
from apps.candidates.models import CandidateAttributeVote


@pytest.mark.django_db
def test_landing_is_public(client, candidate_factory):
    candidate_factory()

    response = client.get(reverse("landing"))

    assert response.status_code == 200
    assert "candidate_count" in response.context
    assert "recruiter_count" in response.context
    assert "total_votes" in response.context


@pytest.mark.django_db
def test_dashboard_redirects_anonymous(client):
    response = client.get(reverse("dashboard"))
    assert response.status_code == 302
    assert reverse("account_login") in response.url


@pytest.mark.django_db
def test_dashboard_context_for_authenticated_user(client, recruiter_factory, candidate_factory, attribute_factory):
    user = recruiter_factory()
    client.force_login(user)
    candidate = candidate_factory()
    attr = attribute_factory(code=1, slug="reliable", label="Reliable")
    CandidateAttributeVote.objects.create(candidate=candidate, attribute=attr, recruiter=user)

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert "recent_votes" in response.context
    assert "attributes" in response.context
    assert "hair_colors" in response.context


@pytest.mark.django_db
def test_dashboard_includes_pending_relays(client, recruiter_factory):
    target = recruiter_factory(email="target@example.com")
    initiator = recruiter_factory(email="initiator@example.com")
    client.force_login(target)

    RecruiterContactRelay.objects.create(initiator=initiator, target=target, candidate_id=1)

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert len(response.context["pending_relays_incoming"]) == 1


@pytest.mark.django_db
def test_vote_history_requires_login(client):
    response = client.get(reverse("vote_history"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_vote_history_paginates(client, recruiter_factory, candidate_factory, attribute_factory):
    user = recruiter_factory()
    client.force_login(user)
    attr = attribute_factory(code=2, slug="smart", label="Smart")

    for _ in range(60):
        candidate = candidate_factory()
        CandidateAttributeVote.objects.create(candidate=candidate, attribute=attr, recruiter=user, is_anonymous=False)

    response = client.get(reverse("vote_history"), {"page": 2})

    assert response.status_code == 200
    assert response.context["page_obj"].number == 2


@pytest.mark.django_db
def test_admin_dashboard_requires_staff(client):
    response = client.get(reverse("admin_dashboard"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_admin_dashboard_for_staff(client, superuser):
    client.force_login(superuser)
    response = client.get(reverse("admin_dashboard"))

    assert response.status_code == 200
    assert "stats" in response.context
    assert "nodes" in response.context


@pytest.mark.django_db
def test_profile_page_404_for_unknown_candidate(client):
    response = client.get(reverse("candidate_profile", kwargs={"candidate_id": 99999}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_profile_page_200_and_context(client, candidate_factory):
    candidate = candidate_factory()
    response = client.get(reverse("candidate_profile", kwargs={"candidate_id": candidate.id}))

    assert response.status_code == 200
    assert response.context["candidate"].id == candidate.id
    assert "grouped_votes" in response.context

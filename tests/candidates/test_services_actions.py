from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from apps.accounts.models import RecruiterContactRelay
from apps.candidates.models import CandidateAttributeVote, LookupSession
from apps.candidates.services import cast_votes, create_candidate_record, reveal_profile, submit_candidate_enrichment


@pytest.mark.django_db
def test_reveal_profile_requires_existing_session():
    ok, data = reveal_profile(token=uuid4().hex, ip="127.0.0.1", user=None)
    assert ok is False
    assert "not found" in data["error"].lower()


@pytest.mark.django_db
def test_reveal_profile_rejects_ip_mismatch(candidate_factory, lookup_session_factory):
    candidate = candidate_factory()
    session = lookup_session_factory(
        candidate=candidate,
        matched_candidate=candidate,
        status=LookupSession.Status.RESOLVED,
        profile_expires_at=timezone.now() + timedelta(minutes=2),
    )

    ok, data = reveal_profile(token=session.token.hex, ip="8.8.8.8", user=None)
    assert ok is False
    assert "mismatch" in data["error"].lower()


@pytest.mark.django_db
def test_reveal_profile_rejects_expired_window(candidate_factory, lookup_session_factory):
    candidate = candidate_factory()
    session = lookup_session_factory(
        candidate=candidate,
        matched_candidate=candidate,
        status=LookupSession.Status.RESOLVED,
        profile_expires_at=timezone.now() - timedelta(seconds=1),
    )

    ok, data = reveal_profile(token=session.token.hex, ip=session.requester_ip, user=None)
    assert ok is False
    assert "expired" in data["error"].lower()


@pytest.mark.django_db
def test_reveal_profile_success_increments_counters(candidate_factory, lookup_session_factory, recruiter_factory):
    candidate = candidate_factory(profile_views_count=0)
    recruiter = recruiter_factory()
    session = lookup_session_factory(
        candidate=candidate,
        requester=recruiter,
        matched_candidate=candidate,
        status=LookupSession.Status.RESOLVED,
        profile_expires_at=timezone.now() + timedelta(minutes=2),
    )

    ok, data = reveal_profile(token=session.token.hex, ip=session.requester_ip, user=recruiter)

    assert ok is True
    assert data["id"] == candidate.id
    candidate.refresh_from_db()
    assert candidate.profile_views_count == 1


@pytest.mark.django_db
def test_cast_votes_requires_authenticated_user(candidate_factory):
    ok, data = cast_votes(candidate_id=candidate_factory().id, recruiter=AnonymousUser(), attribute_codes=[1], anonymous=False)
    assert ok is False
    assert "Authentication" in data["error"]


@pytest.mark.django_db
def test_cast_votes_requires_verified_recruiter(recruiter_factory, candidate_factory):
    recruiter = recruiter_factory(is_verified_recruiter=False)
    candidate = candidate_factory()

    ok, data = cast_votes(candidate_id=candidate.id, recruiter=recruiter, attribute_codes=[1], anonymous=False)
    assert ok is False
    assert "verification" in data["error"].lower()


@pytest.mark.django_db
def test_cast_votes_rejects_invalid_attribute_count(recruiter_factory, candidate_factory):
    recruiter = recruiter_factory()
    candidate = candidate_factory()

    ok, data = cast_votes(candidate_id=candidate.id, recruiter=recruiter, attribute_codes=[], anonymous=False)
    assert ok is False
    assert "between 1 and 3" in data["error"]


@pytest.mark.django_db
def test_cast_votes_rejects_duplicate_vote(recruiter_factory, candidate_factory, attribute_factory):
    recruiter = recruiter_factory()
    candidate = candidate_factory()
    attr = attribute_factory(code=300)

    CandidateAttributeVote.objects.create(candidate=candidate, attribute=attr, recruiter=recruiter)
    ok, data = cast_votes(candidate_id=candidate.id, recruiter=recruiter, attribute_codes=[300], anonymous=False)

    assert ok is False
    assert "already voted" in data["error"].lower()


@pytest.mark.django_db
def test_cast_votes_success_and_creates_contact_relay(recruiter_factory, candidate_factory, attribute_factory, monkeypatch):
    prior = recruiter_factory(email="prior@example.com", notify_on_vote_overlap=True)
    recruiter = recruiter_factory(email="new@example.com")
    candidate = candidate_factory()
    prior_attr = attribute_factory(code=301)
    new_attr = attribute_factory(code=302)

    CandidateAttributeVote.objects.create(candidate=candidate, attribute=prior_attr, recruiter=prior)

    sent = []
    monkeypatch.setattr("apps.candidates.services.send_mail", lambda **kwargs: sent.append(kwargs))

    ok, data = cast_votes(candidate_id=candidate.id, recruiter=recruiter, attribute_codes=[302], anonymous=True)

    assert ok is True
    assert data["vote_count"] == 1
    assert RecruiterContactRelay.objects.filter(candidate_id=candidate.id, target=recruiter).count() == 1
    assert len(sent) == 1


@pytest.mark.django_db
def test_create_candidate_record_requires_auth():
    ok, data = create_candidate_record(payload={}, recruiter=AnonymousUser())
    assert ok is False
    assert "Authentication" in data["error"]


@pytest.mark.django_db
def test_create_candidate_record_requires_mandatory_fields(recruiter_factory):
    ok, data = create_candidate_record(payload={"first_name": "Only"}, recruiter=recruiter_factory())
    assert ok is False
    assert "Missing required fields" in data["error"]


@pytest.mark.django_db
def test_create_candidate_record_success_awards_credits(recruiter_factory):
    recruiter = recruiter_factory(credits=0)
    ok, data = create_candidate_record(
        payload={
            "first_name": "Nora",
            "last_name": "Fischer",
            "gender": "female",
            "country": "Germany",
            "region": "Bayern",
            "city": "Munich",
        },
        recruiter=recruiter,
    )

    assert ok is True
    recruiter.refresh_from_db()
    assert recruiter.credits == 2
    assert data["credits_awarded"] == 2


@pytest.mark.django_db
def test_submit_candidate_enrichment_requires_auth(candidate_factory):
    ok, data = submit_candidate_enrichment(candidate_id=candidate_factory().id, payload={"city": "Hamburg"}, recruiter=AnonymousUser())
    assert ok is False


@pytest.mark.django_db
def test_submit_candidate_enrichment_candidate_not_found(recruiter_factory):
    ok, data = submit_candidate_enrichment(candidate_id=99999, payload={"city": "Hamburg"}, recruiter=recruiter_factory())
    assert ok is False
    assert "not found" in data["error"].lower()


@pytest.mark.django_db
def test_submit_candidate_enrichment_rejects_empty_editable_payload(recruiter_factory, candidate_factory):
    recruiter = recruiter_factory()
    candidate = candidate_factory()

    ok, data = submit_candidate_enrichment(candidate_id=candidate.id, payload={"first_name": "Nope"}, recruiter=recruiter)
    assert ok is False


@pytest.mark.django_db
def test_submit_candidate_enrichment_awards_credit_for_two_fields(recruiter_factory, candidate_factory):
    recruiter = recruiter_factory(credits=0)
    candidate = candidate_factory()

    ok, data = submit_candidate_enrichment(
        candidate_id=candidate.id,
        payload={"city": "Hamburg", "secondary_email": "new@example.com"},
        recruiter=recruiter,
    )

    assert ok is True
    recruiter.refresh_from_db()
    assert recruiter.credits == 1
    assert "submission_id" in data

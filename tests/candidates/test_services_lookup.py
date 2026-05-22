from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from apps.candidates.models import CandidateViewLog, LookupSession
from apps.candidates.services import advance_lookup_session, create_lookup_session


@pytest.mark.django_db
def test_create_lookup_session_requires_initial_fields():
    ok, data = create_lookup_session(payload={"country": "Germany"}, user=AnonymousUser(), ip="127.0.0.1")

    assert ok is False
    assert "required" in data["error"]


@pytest.mark.django_db
def test_create_lookup_session_blocks_anonymous_after_daily_view(candidate_factory):
    candidate = candidate_factory()
    CandidateViewLog.objects.create(candidate=candidate, recruiter=None, ip="127.0.0.1")

    ok, data = create_lookup_session(
        payload={"country": "Germany", "region": "Berlin", "first_name": candidate.first_name, "gender": candidate.gender},
        user=AnonymousUser(),
        ip="127.0.0.1",
    )

    assert ok is False
    assert "Anonyme Nutzer" in data["error"]


@pytest.mark.django_db
def test_create_lookup_session_success_for_authenticated_user(recruiter_factory, candidate_factory):
    recruiter = recruiter_factory(last_lookup_on=None)
    candidate = candidate_factory(first_name="Clara")

    ok, data = create_lookup_session(
        payload={
            "country": candidate.country,
            "region": candidate.region,
            "first_name": "Clara",
            "gender": candidate.gender,
        },
        user=recruiter,
        ip="127.0.0.1",
    )

    assert ok is True
    assert data["candidate_count"] >= 1
    recruiter.refresh_from_db()
    assert recruiter.last_lookup_on == timezone.localdate()


@pytest.mark.django_db
def test_create_lookup_session_blocks_authenticated_user_without_credits_on_second_lookup(recruiter_factory, candidate_factory):
    recruiter = recruiter_factory(last_lookup_on=timezone.localdate(), credits=0)
    candidate = candidate_factory(first_name="Clara")

    ok, data = create_lookup_session(
        payload={
            "country": candidate.country,
            "region": candidate.region,
            "first_name": "Clara",
            "gender": candidate.gender,
        },
        user=recruiter,
        ip="127.0.0.1",
    )

    assert ok is False
    assert "Keine Credits" in data["error"]


@pytest.mark.django_db
def test_create_lookup_session_consumes_credit_for_second_daily_lookup(recruiter_factory, candidate_factory):
    recruiter = recruiter_factory(last_lookup_on=timezone.localdate(), credits=2)
    candidate = candidate_factory(first_name="Clara")

    ok, data = create_lookup_session(
        payload={
            "country": candidate.country,
            "region": candidate.region,
            "first_name": "Clara",
            "gender": candidate.gender,
        },
        user=recruiter,
        ip="127.0.0.1",
    )

    assert ok is True
    recruiter.refresh_from_db()
    assert recruiter.credits == 1
    assert data["candidate_count"] >= 1


@pytest.mark.django_db
def test_advance_lookup_session_rejects_invalid_session():
    ok, data = advance_lookup_session(
        token=uuid4().hex,
        payload={"step": 2, "case_type": "email", "email": "a@b.c"},
        ip="127.0.0.1",
    )
    assert ok is False
    assert "invalid" in data["error"].lower()


@pytest.mark.django_db
def test_advance_lookup_session_rejects_invalid_case_type(lookup_session_factory):
    session = lookup_session_factory()

    ok, data = advance_lookup_session(
        token=session.token.hex,
        payload={"step": 2, "case_type": "unknown", "email": "a@b.c"},
        ip=session.requester_ip,
    )

    assert ok is False
    assert "case_type" in data["error"]


@pytest.mark.django_db
def test_advance_lookup_session_marks_failed_when_no_match(candidate_factory, lookup_session_factory):
    candidate = candidate_factory(first_name="Clara", last_name="Mueller", city="Berlin")
    session = lookup_session_factory(candidate=candidate)

    ok, data = advance_lookup_session(
        token=session.token.hex,
        payload={"step": 2, "case_type": "lastname", "last_name": "Wrong"},
        ip=session.requester_ip,
    )

    assert ok is False
    assert "No candidate matches" in data["error"]
    session.refresh_from_db()
    assert session.status == LookupSession.Status.FAILED


@pytest.mark.django_db
def test_advance_lookup_session_resolves_lastname_pipeline(candidate_factory, lookup_session_factory):
    candidate = candidate_factory(first_name="Clara", last_name="Mueller", city="Berlin")
    session = lookup_session_factory(candidate=candidate)

    ok2, step2 = advance_lookup_session(
        token=session.token.hex,
        payload={"step": 2, "case_type": "lastname", "last_name": "Müller"},
        ip=session.requester_ip,
    )
    assert ok2 is True
    assert step2["resolved"] is False

    ok3, step3 = advance_lookup_session(
        token=session.token.hex,
        payload={"step": 3, "case_type": "lastname", "city": "Berlin"},
        ip=session.requester_ip,
    )
    assert ok3 is True
    assert step3["resolved"] is True


@pytest.mark.django_db
def test_advance_lookup_session_expires_step(candidate_factory, lookup_session_factory):
    candidate = candidate_factory(first_name="Clara")
    session = lookup_session_factory(candidate=candidate, step_expires_at=timezone.now() - timedelta(seconds=1))

    ok, data = advance_lookup_session(
        token=session.token.hex,
        payload={"step": 2, "case_type": "lastname", "last_name": "Mueller"},
        ip=session.requester_ip,
    )

    assert ok is False
    assert "expired" in data["error"].lower()

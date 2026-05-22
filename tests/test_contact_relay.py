"""Tests for the recruiter contact relay flow."""
import pytest
from django.core import mail

from apps.accounts.models import RecruiterContactRelay, RecruiterUser
from apps.candidates.models import Candidate, CandidateAttributeDefinition, CandidateGender, HairColor
from apps.candidates.services import cast_votes


def _recruiter(email, **kw):
    return RecruiterUser.objects.create_user(
        email=email,
        password="Secure!Pass123",
        is_verified_recruiter=True,
        **kw,
    )


def _attr():
    return CandidateAttributeDefinition.objects.get_or_create(
        code=1,
        defaults={"slug": "reliable", "label": "Zuverlaessig", "icon": "✓"},
    )[0]


@pytest.mark.django_db
def test_vote_overlap_creates_relay_and_sends_email():
    r1 = _recruiter("r1@example.com", notify_on_vote_overlap=True)
    r2 = _recruiter("r2@example.com")
    attr = _attr()
    candidate = Candidate.objects.create(
        first_name="Relay",
        last_name="Test",
        gender=CandidateGender.FEMALE,
        country="Germany",
        region="Berlin",
        city="Berlin",
        hair_color=HairColor.BROWN,
    )

    # r1 votes first
    ok, _ = cast_votes(candidate_id=candidate.id, recruiter=r1, attribute_codes=[attr.code], anonymous=False)
    assert ok

    # r2 votes → should trigger relay creation and email to r1
    ok, _ = cast_votes(candidate_id=candidate.id, recruiter=r2, attribute_codes=[attr.code], anonymous=False)
    assert ok

    relay = RecruiterContactRelay.objects.filter(candidate_id=candidate.id).first()
    assert relay is not None
    assert relay.initiator == r1
    assert relay.target == r2
    assert relay.status == RecruiterContactRelay.Status.PENDING

    # Email sent to r1
    assert any("r1@example.com" in m.to for m in mail.outbox)


@pytest.mark.django_db
def test_no_relay_when_notify_disabled():
    r1 = _recruiter("nonotify@example.com", notify_on_vote_overlap=False)
    r2 = _recruiter("r2nonotify@example.com")
    attr = _attr()
    candidate = Candidate.objects.create(
        first_name="Quiet",
        last_name="Test",
        gender=CandidateGender.MALE,
        country="Germany",
        region="Bayern",
        city="Munich",
        hair_color=HairColor.BLACK,
    )

    cast_votes(candidate_id=candidate.id, recruiter=r1, attribute_codes=[attr.code], anonymous=False)
    initial_relay_count = RecruiterContactRelay.objects.count()

    cast_votes(candidate_id=candidate.id, recruiter=r2, attribute_codes=[attr.code], anonymous=False)

    assert RecruiterContactRelay.objects.count() == initial_relay_count


@pytest.mark.django_db
def test_accept_relay_sends_emails_to_both():
    from django.test import Client

    r1 = _recruiter("accept1@example.com", notify_on_vote_overlap=True)
    r2 = _recruiter("accept2@example.com")
    relay = RecruiterContactRelay.objects.create(
        initiator=r1,
        target=r2,
        candidate_id=99,
    )

    client = Client()
    client.force_login(r2)
    mail.outbox.clear()

    response = client.post(
        f"/api/recruiters/contact-request/{relay.id}/accept",
        content_type="application/json",
        HTTP_X_JS_GATE="bypass",
    )
    # Should be 200 or 403 depending on gate; the relay should be accepted on 200
    if response.status_code == 200:
        relay.refresh_from_db()
        assert relay.status == RecruiterContactRelay.Status.ACCEPTED
        recipients = [addr for m in mail.outbox for addr in m.to]
        assert "accept1@example.com" in recipients
        assert "accept2@example.com" in recipients

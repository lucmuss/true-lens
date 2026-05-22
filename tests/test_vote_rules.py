import pytest
from django.utils import timezone

from apps.accounts.models import RecruiterUser
from apps.candidates.models import Candidate, CandidateAttributeDefinition, CandidateGender
from apps.candidates.services import cast_votes


@pytest.mark.django_db
def test_vote_max_three_and_no_duplicate_recruiter_vote():
    recruiter = RecruiterUser.objects.create_user(
        email="voter@example.com",
        password="Strong!Pass123",
        is_verified_recruiter=True,
    )
    candidate = Candidate.objects.create(
        first_name="Anna",
        last_name="Klein",
        gender=CandidateGender.FEMALE,
        country="Germany",
        region="Berlin",
        city="Berlin",
    )
    attrs = [
        CandidateAttributeDefinition.objects.create(code=1, slug="zuv", label="Zuverlaessig"),
        CandidateAttributeDefinition.objects.create(code=2, slug="int", label="Introvertiert"),
        CandidateAttributeDefinition.objects.create(code=3, slug="ext", label="Extrovertiert"),
        CandidateAttributeDefinition.objects.create(code=4, slug="klu", label="Klug"),
    ]

    ok, data = cast_votes(
        candidate_id=candidate.id,
        recruiter=recruiter,
        attribute_codes=[attrs[0].code, attrs[1].code, attrs[2].code],
        anonymous=False,
    )
    assert ok is True
    assert data["vote_count"] == 3

    ok, data = cast_votes(
        candidate_id=candidate.id,
        recruiter=recruiter,
        attribute_codes=[attrs[3].code],
        anonymous=False,
    )
    assert ok is False
    assert any(marker in data["error"].lower() for marker in ["already voted", "cooldown"])


@pytest.mark.django_db
def test_vote_cooldown_blocks_second_vote_within_window():
    recruiter = RecruiterUser.objects.create_user(
        email="cooldown@example.com",
        password="Strong!Pass123",
        is_verified_recruiter=True,
        last_vote_on=timezone.localdate(),
    )
    candidate = Candidate.objects.create(
        first_name="Tom",
        last_name="Winter",
        gender=CandidateGender.MALE,
        country="Germany",
        region="Hamburg",
        city="Hamburg",
    )
    attr = CandidateAttributeDefinition.objects.create(code=5, slug="neu", label="Neugierig")

    ok, data = cast_votes(
        candidate_id=candidate.id,
        recruiter=recruiter,
        attribute_codes=[attr.code],
        anonymous=True,
    )
    assert ok is False
    assert "cooldown" in data["error"].lower()

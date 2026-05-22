from __future__ import annotations

from datetime import date

import pytest
from django.db import IntegrityError
from django.test import override_settings
from django.utils import timezone

from apps.candidates.models import (
    Candidate,
    CandidateAttributeVote,
    CandidateGender,
    HairColor,
    SocialPlatform,
    detect_social_platform,
    normalize_token,
)


@pytest.mark.django_db
def test_normalize_token_removes_diacritics_and_symbols():
    assert normalize_token(" Clarä--Müller ") == "clara muller"


@pytest.mark.django_db
def test_detect_social_platform_for_known_domains():
    assert detect_social_platform("https://www.tinder.com/@abc") == int(SocialPlatform.TINDER)
    assert detect_social_platform("https://subdomain.bumble.com/profile") == int(SocialPlatform.BUMBLE)


@pytest.mark.django_db
def test_detect_social_platform_rejects_invalid_scheme_or_unknown_host():
    assert detect_social_platform("ftp://tinder.com/x") is None
    assert detect_social_platform("https://unknown.example.com") is None


@pytest.mark.django_db
def test_candidate_save_sets_normalized_fields_and_dating_platform(candidate_factory):
    candidate = candidate_factory(
        first_name="Clarä",
        last_name="Müller",
        dating_profile_url="https://hinge.co/user/123",
    )

    assert candidate.first_name_norm == "clara"
    assert candidate.last_name_norm == "muller"
    assert candidate.dating_platform == SocialPlatform.HINGE


@pytest.mark.django_db
def test_candidate_current_age_calculated_from_birth_date(candidate_factory):
    candidate = candidate_factory(birth_date=date(2000, 1, 1), age_years=None)
    assert candidate.current_age == timezone.localdate().year - 2000


@pytest.mark.django_db
def test_candidate_current_age_falls_back_to_age_years(candidate_factory):
    candidate = candidate_factory(birth_date=None, age_years=31)
    assert candidate.current_age == 31


@pytest.mark.django_db
def test_candidate_masked_fields(candidate_factory):
    candidate = candidate_factory(last_name="Meyer", primary_email="ab@example.com", primary_phone="+4912345678")

    assert candidate.masked_last_name == "M***r"
    assert candidate.masked_email == "a*@example.com"
    assert candidate.masked_phone.startswith("+4")
    assert candidate.masked_phone.endswith("78")


@pytest.mark.django_db
def test_candidate_fuzzy_match_handles_umlauts(candidate_factory):
    candidate = candidate_factory(first_name="Clara", last_name="Mueller")
    assert candidate.fuzzy_match_first_name("Clarä") is True
    assert candidate.fuzzy_match_last_name("Müller") is True


@pytest.mark.django_db
def test_candidate_vote_expiry_is_set_from_retention_years(candidate_factory, attribute_factory, recruiter_factory):
    candidate = candidate_factory()
    attr = attribute_factory()
    recruiter = recruiter_factory()

    with override_settings(VOTE_RETENTION_YEARS=5):
        vote = CandidateAttributeVote.objects.create(
            candidate=candidate,
            attribute=attr,
            recruiter=recruiter,
            voted_on=date(2024, 2, 29),
        )

    assert vote.expires_on == date(2029, 2, 28)


@pytest.mark.django_db
def test_candidate_vote_unique_constraint(candidate_factory, attribute_factory, recruiter_factory):
    candidate = candidate_factory()
    attr = attribute_factory()
    recruiter = recruiter_factory()

    CandidateAttributeVote.objects.create(candidate=candidate, attribute=attr, recruiter=recruiter)
    with pytest.raises(IntegrityError):
        CandidateAttributeVote.objects.create(candidate=candidate, attribute=attr, recruiter=recruiter)


@pytest.mark.django_db
def test_public_vote_breakdown_sorts_and_filters_visibility_and_expiry(candidate_factory, attribute_factory, recruiter_factory):
    candidate = candidate_factory()
    recruiter = recruiter_factory()
    attr_top = attribute_factory(code=11, slug="reliable", label="Reliable")
    attr_low = attribute_factory(code=12, slug="smart", label="Smart")

    for _ in range(3):
        CandidateAttributeVote.objects.create(
            candidate=candidate,
            attribute=attr_top,
            recruiter=None,
            is_anonymous=True,
            voted_on=timezone.localdate(),
        )

    CandidateAttributeVote.objects.create(
        candidate=candidate,
        attribute=attr_low,
        recruiter=recruiter,
        voted_on=timezone.localdate(),
    )

    CandidateAttributeVote.objects.create(
        candidate=candidate,
        attribute=attr_low,
        recruiter=None,
        is_anonymous=True,
        is_visible=False,
        voted_on=timezone.localdate(),
    )

    CandidateAttributeVote.objects.create(
        candidate=candidate,
        attribute=attr_low,
        recruiter=None,
        is_anonymous=True,
        voted_on=timezone.localdate(),
        expires_on=timezone.localdate() - timezone.timedelta(days=1),
    )

    rows = candidate.public_vote_breakdown()

    assert rows[0]["label"] == "Reliable"
    assert rows[0]["count"] == 3
    assert rows[1]["label"] == "Smart"
    assert rows[1]["count"] == 1


@pytest.mark.django_db
def test_candidate_str(candidate_factory):
    candidate = candidate_factory(first_name="Anna", last_name="Becker")
    assert str(candidate) == "Anna Becker"


@pytest.mark.django_db
def test_lookup_session_defaults(lookup_session_factory):
    session = lookup_session_factory()
    assert session.status == session.Status.ACTIVE
    assert session.current_step == 1


@pytest.mark.django_db
def test_hair_color_filter_mapping_consistency():
    assert HairColor.BLACK.label == "Schwarz"
    assert int(HairColor.BLACK) == 1


@pytest.mark.django_db
def test_lookup_attempt_created_via_relation(lookup_session_factory):
    session = lookup_session_factory()
    attempt = session.attempts.create(step=2, ip="127.0.0.1", success=True, reason="ok")
    assert attempt.session_id == session.id
    assert attempt.step == 2

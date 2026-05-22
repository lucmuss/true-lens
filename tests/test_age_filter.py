"""Tests for age-based candidate filtering including birth_date-derived ages."""
from datetime import date

import pytest
from django.utils import timezone

from apps.candidates.models import Candidate, CandidateGender, HairColor
from apps.candidates.services import _age_filter, create_lookup_session, advance_lookup_session, reveal_profile


def _make_candidate(**kwargs):
    defaults = dict(
        first_name="Test",
        last_name="Person",
        gender=CandidateGender.FEMALE,
        country="Germany",
        region="Bayern",
        city="Munich",
        hair_color=HairColor.BROWN,
    )
    defaults.update(kwargs)
    return Candidate.objects.create(**defaults)


@pytest.mark.django_db
def test_age_filter_by_age_years():
    c = _make_candidate(age_years=36)
    qs = Candidate.objects.all()
    result = _age_filter(qs, "36")
    assert c in result


@pytest.mark.django_db
def test_age_filter_by_birth_date():
    today = timezone.localdate()
    # Birthday already happened this year -> birth_year = today.year - age
    age = 30
    birth_date = date(today.year - age, today.month, max(1, today.day - 1))
    c = _make_candidate(birth_date=birth_date)
    qs = Candidate.objects.all()
    result = _age_filter(qs, str(age))
    assert c in result


@pytest.mark.django_db
def test_age_filter_by_birth_date_birthday_not_yet():
    today = timezone.localdate()
    age = 25
    # Birthday is in the future this year -> birth_year = today.year - age - 1
    future_month = today.month + 1 if today.month < 12 else 1
    future_year = today.year - age - 1
    birth_date = date(future_year, future_month, 1)
    c = _make_candidate(birth_date=birth_date)
    qs = Candidate.objects.all()
    result = _age_filter(qs, str(age))
    assert c in result


@pytest.mark.django_db
def test_age_filter_wrong_age_excluded():
    c = _make_candidate(age_years=40)
    qs = Candidate.objects.all()
    result = _age_filter(qs, "25")
    assert c not in result


@pytest.mark.django_db
def test_age_filter_invalid_value():
    _make_candidate(age_years=30)
    qs = Candidate.objects.all()
    result = _age_filter(qs, "not_a_number")
    assert result.count() == 0


@pytest.mark.django_db
def test_full_search_flow_age_case():
    from apps.accounts.models import RecruiterUser

    today = timezone.localdate()
    age = 28
    birth_date = date(today.year - age, 1, 1)
    candidate = _make_candidate(
        first_name="Anna",
        last_name="Test",
        birth_date=birth_date,
        city="Munich",
    )
    recruiter = RecruiterUser.objects.create_user(
        email="ageflowtester@example.com",
        password="Secure!Pass123",
        is_verified_recruiter=True,
    )

    ok, data = create_lookup_session(
        payload={"country": "Germany", "region": "Bayern", "first_name": "Anna", "gender": "female"},
        user=recruiter,
        ip="10.0.0.1",
    )
    assert ok
    token = data["session_token"]

    ok, step = advance_lookup_session(
        token=token, ip="10.0.0.1",
        payload={"step": 2, "case_type": "age", "age": str(age)},
    )
    assert ok, step
    assert step["resolved"] is False

    ok, step2 = advance_lookup_session(
        token=token, ip="10.0.0.1",
        payload={"step": 3, "case_type": "age", "city": "Munich"},
    )
    assert ok, step2
    assert step2["resolved"] is True

    ok, profile = reveal_profile(token=token, ip="10.0.0.1", user=recruiter)
    assert ok
    assert profile["id"] == candidate.id

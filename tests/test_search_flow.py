import pytest

from apps.accounts.models import RecruiterUser
from apps.candidates.models import Candidate, CandidateGender, HairColor
from apps.candidates.services import advance_lookup_session, create_lookup_session, reveal_profile


@pytest.mark.django_db
def test_fuzzy_firstname_and_lastname_lookup_flow():
    recruiter = RecruiterUser.objects.create_user(
        email="recruiter@example.com",
        password="Strong!Pass123",
        is_verified_recruiter=True,
    )
    candidate = Candidate.objects.create(
        first_name="Clara",
        last_name="Mueller",
        gender=CandidateGender.FEMALE,
        country="Germany",
        region="Sachsen",
        city="Leipzig",
        hair_color=HairColor.BLONDE,
    )

    ok, data = create_lookup_session(
        payload={
            "country": "Germany",
            "region": "Sachsen",
            "first_name": "Clarä",
            "gender": CandidateGender.FEMALE,
        },
        user=recruiter,
        ip="127.0.0.1",
    )
    assert ok is True
    assert data["candidate_count"] == 1

    token = data["session_token"]
    ok, step2 = advance_lookup_session(
        token=token,
        ip="127.0.0.1",
        payload={
            "step": 2,
            "case_type": "lastname",
            "last_name": "Müller",
        },
    )
    assert ok is True
    assert step2["resolved"] is False

    ok, step3 = advance_lookup_session(
        token=token,
        ip="127.0.0.1",
        payload={
            "step": 3,
            "case_type": "lastname",
            "city": "Leipzig",
        },
    )
    assert ok is True
    assert step3["resolved"] is True

    ok, profile = reveal_profile(token=token, ip="127.0.0.1", user=recruiter)
    assert ok is True
    assert profile["id"] == candidate.id
    assert profile["first_name"] == "Clara"

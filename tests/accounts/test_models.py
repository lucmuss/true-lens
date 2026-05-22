from __future__ import annotations

from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.accounts.models import RecruiterContactRelay, RecruiterSecurityVerification


@pytest.mark.django_db
def test_create_user_requires_email(django_user_model):
    with pytest.raises(ValueError, match="Email address is required"):
        django_user_model.objects.create_user(email="", password="Secure!Pass12345")


@pytest.mark.django_db
def test_create_user_without_password_sets_unusable_password(django_user_model):
    user = django_user_model.objects.create_user(email="nopw@example.com", password=None)
    assert user.has_usable_password() is False


@pytest.mark.django_db
def test_create_superuser_requires_staff_flag(django_user_model):
    with pytest.raises(ValueError, match="is_staff=True"):
        django_user_model.objects.create_superuser(
            email="admin-a@example.com",
            password="Secure!Pass12345",
            is_staff=False,
        )


@pytest.mark.django_db
def test_create_superuser_requires_superuser_flag(django_user_model):
    with pytest.raises(ValueError, match="is_superuser=True"):
        django_user_model.objects.create_superuser(
            email="admin-b@example.com",
            password="Secure!Pass12345",
            is_superuser=False,
        )


@pytest.mark.django_db
def test_user_str_returns_email(recruiter_factory):
    user = recruiter_factory(email="display@example.com")
    assert str(user) == "display@example.com"


@pytest.mark.django_db
def test_add_credits_ignores_non_positive_amount(recruiter_factory):
    user = recruiter_factory(credits=5)
    user.add_credits(0)
    user.add_credits(-4)
    user.refresh_from_db()
    assert user.credits == 5


@pytest.mark.django_db
def test_add_credits_increases_balance(recruiter_factory):
    user = recruiter_factory(credits=1)
    user.add_credits(3)
    user.refresh_from_db()
    assert user.credits == 4


@pytest.mark.django_db
def test_consume_credit_handles_zero_balance(recruiter_factory):
    user = recruiter_factory(credits=0)
    assert user.consume_credit() is False


@pytest.mark.django_db
def test_consume_credit_decrements_and_returns_true(recruiter_factory):
    user = recruiter_factory(credits=2)
    assert user.consume_credit() is True
    user.refresh_from_db()
    assert user.credits == 1


@pytest.mark.django_db
@override_settings(VOTE_COOLDOWN_DAYS=3)
def test_can_vote_today_respects_configured_cooldown(recruiter_factory):
    user = recruiter_factory()
    user.last_vote_on = timezone.localdate() - timedelta(days=2)
    assert user.can_vote_today() is False

    user.last_vote_on = timezone.localdate() - timedelta(days=3)
    assert user.can_vote_today() is True


@pytest.mark.django_db
def test_mark_vote_sets_today(recruiter_factory):
    user = recruiter_factory(last_vote_on=None)
    user.mark_vote()
    user.refresh_from_db()
    assert user.last_vote_on == timezone.localdate()


@pytest.mark.django_db
def test_mark_lookup_sets_today(recruiter_factory):
    user = recruiter_factory(last_lookup_on=None)
    user.mark_lookup()
    user.refresh_from_db()
    assert user.last_lookup_on == timezone.localdate()


@pytest.mark.django_db
def test_can_lookup_today_blocks_second_lookup_same_day(recruiter_factory):
    user = recruiter_factory(last_lookup_on=timezone.localdate())
    assert user.can_lookup_today() is False


@pytest.mark.django_db
@override_settings(AUTH_NEW_RECORDS_PER_WEEK=1)
def test_can_create_profile_this_week_enforces_limit(recruiter_factory):
    user = recruiter_factory(
        weekly_profile_creates=1,
        weekly_profile_creates_anchor=timezone.localdate(),
    )
    assert user.can_create_profile_this_week() is False


@pytest.mark.django_db
def test_mark_profile_created_resets_window_after_seven_days(recruiter_factory):
    user = recruiter_factory(
        weekly_profile_creates=3,
        weekly_profile_creates_anchor=timezone.localdate() - timedelta(days=8),
    )
    user.mark_profile_created()
    user.refresh_from_db()
    assert user.weekly_profile_creates == 1
    assert user.weekly_profile_creates_anchor == timezone.localdate()


@pytest.mark.django_db
def test_security_verification_mark_completed_updates_timestamp(recruiter_factory):
    verification = RecruiterSecurityVerification.objects.create(
        recruiter=recruiter_factory(),
        code="123456",
        expires_at=timezone.now() + timedelta(minutes=5),
    )

    verification.mark_completed()
    verification.refresh_from_db()

    assert verification.is_completed is True
    assert verification.completed_at is not None


@pytest.mark.django_db
def test_security_verification_expired_returns_true(recruiter_factory):
    verification = RecruiterSecurityVerification.objects.create(
        recruiter=recruiter_factory(),
        code="123456",
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    assert verification.is_expired() is True


@pytest.mark.django_db
def test_contact_relay_defaults_to_pending(recruiter_factory):
    initiator = recruiter_factory(email="init@example.com")
    target = recruiter_factory(email="target@example.com")
    relay = RecruiterContactRelay.objects.create(initiator=initiator, target=target, candidate_id=42)

    assert relay.status == RecruiterContactRelay.Status.PENDING
    assert relay.resolved_at is None

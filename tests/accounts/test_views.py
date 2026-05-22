from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import RecruiterSecurityVerification


@pytest.mark.django_db
def test_security_verify_redirects_when_already_completed(client, recruiter_factory):
    user = recruiter_factory()
    verification = RecruiterSecurityVerification.objects.create(
        recruiter=user,
        code="123456",
        expires_at=timezone.now() + timedelta(minutes=10),
        is_completed=True,
    )

    response = client.get(reverse("account_security_verify", kwargs={"token": verification.token.hex}))

    assert response.status_code == 302
    assert reverse("account_login") in response.url


@pytest.mark.django_db
def test_security_verify_get_renders_form(client, recruiter_factory, monkeypatch):
    user = recruiter_factory()
    verification = RecruiterSecurityVerification.objects.create(
        recruiter=user,
        code="123456",
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    monkeypatch.setattr("apps.accounts.views.create_captcha_inline", lambda _request: {"captcha_id": "cid"})

    response = client.get(reverse("account_security_verify", kwargs={"token": verification.token.hex}))

    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_security_verify_rejects_invalid_captcha(client, recruiter_factory, monkeypatch):
    user = recruiter_factory()
    verification = RecruiterSecurityVerification.objects.create(
        recruiter=user,
        code="123456",
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    monkeypatch.setattr("apps.accounts.views.create_captcha_inline", lambda _request: {"captcha_id": "cid"})
    monkeypatch.setattr("apps.accounts.views.verify_captcha_inline", lambda *args, **kwargs: False)

    response = client.post(
        reverse("account_security_verify", kwargs={"token": verification.token.hex}),
        data={"captcha_id": "cid", "captcha_answer": "AAAA", "code": "123456"},
    )

    assert response.status_code == 200
    verification.refresh_from_db()
    assert verification.is_completed is False


@pytest.mark.django_db
def test_security_verify_rejects_expired_code(client, recruiter_factory, monkeypatch):
    user = recruiter_factory()
    verification = RecruiterSecurityVerification.objects.create(
        recruiter=user,
        code="123456",
        expires_at=timezone.now() - timedelta(minutes=1),
    )

    monkeypatch.setattr("apps.accounts.views.create_captcha_inline", lambda _request: {"captcha_id": "cid"})
    monkeypatch.setattr("apps.accounts.views.verify_captcha_inline", lambda *args, **kwargs: True)

    response = client.post(
        reverse("account_security_verify", kwargs={"token": verification.token.hex}),
        data={"captcha_id": "cid", "captcha_answer": "AAAA", "code": "123456"},
    )

    assert response.status_code == 200
    verification.refresh_from_db()
    assert verification.is_completed is False


@pytest.mark.django_db
def test_security_verify_rejects_wrong_code(client, recruiter_factory, monkeypatch):
    user = recruiter_factory()
    verification = RecruiterSecurityVerification.objects.create(
        recruiter=user,
        code="123456",
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    monkeypatch.setattr("apps.accounts.views.create_captcha_inline", lambda _request: {"captcha_id": "cid"})
    monkeypatch.setattr("apps.accounts.views.verify_captcha_inline", lambda *args, **kwargs: True)

    response = client.post(
        reverse("account_security_verify", kwargs={"token": verification.token.hex}),
        data={"captcha_id": "cid", "captcha_answer": "AAAA", "code": "000000"},
    )

    assert response.status_code == 200
    verification.refresh_from_db()
    assert verification.is_completed is False


@pytest.mark.django_db
def test_security_verify_success_marks_recruiter_verified(client, recruiter_factory, monkeypatch):
    user = recruiter_factory(is_verified_recruiter=False)
    verification = RecruiterSecurityVerification.objects.create(
        recruiter=user,
        code="123456",
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    monkeypatch.setattr("apps.accounts.views.create_captcha_inline", lambda _request: {"captcha_id": "cid"})
    monkeypatch.setattr("apps.accounts.views.verify_captcha_inline", lambda *args, **kwargs: True)

    response = client.post(
        reverse("account_security_verify", kwargs={"token": verification.token.hex}),
        data={"captcha_id": "cid", "captcha_answer": "AAAA", "code": "123456"},
    )

    assert response.status_code == 302
    user.refresh_from_db()
    verification.refresh_from_db()
    assert user.is_verified_recruiter is True
    assert verification.is_completed is True


@pytest.mark.django_db
def test_recruiter_settings_requires_login(client):
    response = client.get(reverse("recruiter_settings"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_recruiter_settings_post_updates_flags(client, recruiter_factory):
    user = recruiter_factory(
        notify_on_vote_overlap=True,
        notify_on_contact_requests=True,
        notify_on_security=True,
    )
    client.force_login(user)

    response = client.post(
        reverse("recruiter_settings"),
        data={"notify_on_vote_overlap": "on"},
    )

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.notify_on_vote_overlap is True
    assert user.notify_on_contact_requests is False
    assert user.notify_on_security is False


@pytest.mark.django_db
def test_delete_profile_get_and_post(client, recruiter_factory):
    user = recruiter_factory(email="delete-me@example.com", display_name="DeleteMe")
    client.force_login(user)

    get_response = client.get(reverse("recruiter_delete"))
    assert get_response.status_code == 200

    post_response = client.post(reverse("recruiter_delete"))
    assert post_response.status_code == 302

    user.refresh_from_db()
    assert user.is_active is False
    assert user.deleted_at is not None
    assert user.email.endswith("@invalid.local")

from __future__ import annotations

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.security.models import ApiGateToken, IPBan, SecurityEvent


@pytest.mark.django_db
def test_ipban_unique_ip_constraint(ip_ban_factory):
    ip_ban_factory(ip="10.10.10.1")
    with pytest.raises(IntegrityError):
        ip_ban_factory(ip="10.10.10.1")


@pytest.mark.django_db
def test_api_gate_token_defaults():
    token = ApiGateToken.objects.create(
        token="tok-1",
        ip="127.0.0.1",
        user_agent_hash="abc",
        expires_at=timezone.now() + timezone.timedelta(minutes=1),
    )
    assert token.rotation_counter == 0
    assert token.last_seen_at is not None


@pytest.mark.django_db
def test_security_event_payload_persists(recruiter_factory):
    user = recruiter_factory()
    event = SecurityEvent.objects.create(
        event_type=SecurityEvent.EventType.CAPTCHA_SOLVED,
        ip="127.0.0.1",
        user=user,
        payload={"captcha_id": "xyz"},
    )
    assert event.payload == {"captcha_id": "xyz"}


@pytest.mark.django_db
def test_security_event_type_choices_exist():
    names = {choice[0] for choice in SecurityEvent.EventType.choices}
    assert "captcha_failed" in names
    assert "ip_banned" in names

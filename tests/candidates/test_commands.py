from __future__ import annotations

import io
import json
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from apps.candidates.models import CandidateAttributeDefinition, CandidateAttributeVote


@pytest.mark.django_db
def test_seed_attribute_definitions_updates_existing_and_creates_missing(tmp_path):
    config_path = tmp_path / "attributes.json"
    config_path.write_text(
        json.dumps(
            [
                {"code": 1, "slug": "reliable", "label": "Reliable", "icon": "check"},
                {"code": 2, "slug": "smart", "label": "Smart", "icon": "brain"},
            ]
        ),
        encoding="utf-8",
    )

    existing = CandidateAttributeDefinition.objects.create(
        code=1,
        slug="old-reliable",
        label="Old",
        icon="old",
        is_active=False,
    )

    with override_settings(CANDIDATE_ATTRIBUTE_CONFIG_PATH=str(config_path)):
        call_command("seed_attribute_definitions", stdout=io.StringIO())

    existing.refresh_from_db()
    assert existing.slug == "reliable"
    assert existing.label == "Reliable"
    assert existing.icon == "check"
    assert existing.is_active is True

    created = CandidateAttributeDefinition.objects.get(code=2)
    assert created.slug == "smart"
    assert created.label == "Smart"


@pytest.mark.django_db
def test_seed_attribute_definitions_handles_invalid_json_gracefully(tmp_path):
    config_path = tmp_path / "invalid.json"
    config_path.write_text("not-json", encoding="utf-8")

    with override_settings(CANDIDATE_ATTRIBUTE_CONFIG_PATH=str(config_path)):
        call_command("seed_attribute_definitions", stdout=io.StringIO())

    assert CandidateAttributeDefinition.objects.count() == 0


@pytest.mark.django_db
def test_hide_expired_votes_hides_only_visible_expired_votes(candidate_factory, attribute_factory):
    candidate = candidate_factory()
    attr_expired = attribute_factory(code=11)
    attr_future = attribute_factory(code=12)
    attr_hidden = attribute_factory(code=13)

    today = timezone.localdate()
    expired_visible = CandidateAttributeVote.objects.create(
        candidate=candidate,
        attribute=attr_expired,
        is_visible=True,
        voted_on=today - timedelta(days=10),
        expires_on=today,
    )
    future_visible = CandidateAttributeVote.objects.create(
        candidate=candidate,
        attribute=attr_future,
        is_visible=True,
        voted_on=today,
        expires_on=today + timedelta(days=2),
    )
    already_hidden = CandidateAttributeVote.objects.create(
        candidate=candidate,
        attribute=attr_hidden,
        is_visible=False,
        voted_on=today - timedelta(days=20),
        expires_on=today - timedelta(days=1),
    )

    out = io.StringIO()
    call_command("hide_expired_votes", stdout=out)

    expired_visible.refresh_from_db()
    future_visible.refresh_from_db()
    already_hidden.refresh_from_db()

    assert expired_visible.is_visible is False
    assert future_visible.is_visible is True
    assert already_hidden.is_visible is False
    assert "Expired votes hidden: 1" in out.getvalue()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_seed_dev_data_enforces_minimum_random_password_length():
    out = io.StringIO()

    call_command("seed_dev_data", "--clear", "--random-password-length", "4", stdout=out)

    line = next((ln for ln in out.getvalue().splitlines() if "recruiter1@example.com / " in ln), "")
    assert line
    generated_password = line.split(" / ", 1)[1].strip()
    assert len(generated_password) >= 12

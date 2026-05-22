from __future__ import annotations

import pytest

from apps.accounts.forms import RecruiterNotificationSettingsForm
from apps.accounts.password_validators import SpecialCharacterValidator
from apps.security.forms import CaptchaInlineForm


@pytest.mark.django_db
def test_captcha_inline_form_valid_with_required_fields():
    form = CaptchaInlineForm(data={"captcha_id": "abc", "captcha_answer": "A1B2", "code": "123456"})
    assert form.is_valid() is True


@pytest.mark.django_db
def test_captcha_inline_form_invalid_without_code():
    form = CaptchaInlineForm(data={"captcha_id": "abc", "captcha_answer": "A1B2"})
    assert form.is_valid() is False
    assert "code" in form.errors


@pytest.mark.django_db
def test_notification_settings_form_maps_missing_values_to_false():
    form = RecruiterNotificationSettingsForm(data={})
    assert form.is_valid() is True
    assert form.cleaned_data["notify_on_vote_overlap"] is False
    assert form.cleaned_data["notify_on_contact_requests"] is False
    assert form.cleaned_data["notify_on_security"] is False


@pytest.mark.django_db
def test_notification_settings_form_accepts_checkbox_values():
    form = RecruiterNotificationSettingsForm(
        data={
            "notify_on_vote_overlap": "on",
            "notify_on_contact_requests": "on",
            "notify_on_security": "on",
        }
    )
    assert form.is_valid() is True
    assert all(form.cleaned_data.values())


@pytest.mark.django_db
def test_special_character_validator_rejects_alnum_password():
    validator = SpecialCharacterValidator()
    with pytest.raises(Exception):
        validator.validate("OnlyLetters123")


@pytest.mark.django_db
def test_special_character_validator_accepts_password_with_symbol():
    validator = SpecialCharacterValidator()
    validator.validate("Valid!Password123")


@pytest.mark.django_db
def test_special_character_validator_help_text():
    validator = SpecialCharacterValidator()
    assert "special character" in validator.get_help_text().lower()

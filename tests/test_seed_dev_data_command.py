import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

User = get_user_model()


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_seed_dev_data_requires_force_in_production_mode():
    with pytest.raises(CommandError, match='--force'):
        call_command('seed_dev_data')


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_seed_dev_data_with_force_generates_random_passwords():
    out = io.StringIO()

    call_command('seed_dev_data', '--force', stdout=out)

    output = out.getvalue()
    line = next((ln for ln in output.splitlines() if 'recruiter1@example.com / ' in ln), '')
    assert line

    password = line.split(' / ', 1)[1].strip()
    assert len(password) >= 12

    user = User.objects.get(email='recruiter1@example.com')
    assert user.check_password(password)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_seed_dev_data_accepts_explicit_password_override():
    shared_password = 'MyS3cure!Password42'

    call_command('seed_dev_data', '--password', shared_password, stdout=io.StringIO())

    for email in ('recruiter1@example.com', 'recruiter2@example.com', 'admin@example.com'):
        user = User.objects.get(email=email)
        assert user.check_password(shared_password)

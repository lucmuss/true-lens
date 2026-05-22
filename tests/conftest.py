from __future__ import annotations

from datetime import timedelta
from itertools import count

import pytest
from django.test import Client
from django.utils import timezone

from apps.candidates.models import Candidate, CandidateAttributeDefinition, CandidateGender, HairColor, LookupSession
from apps.replication.models import NodeInstance
from apps.security.models import CaptchaChallenge, IPBan
from apps.security.services import _digest, create_js_gate_token


_email_seq = count(1)
_candidate_seq = count(1)
_attribute_seq = count(1000)
_node_seq = count(1)


@pytest.fixture
def recruiter_factory(django_user_model):
    def make_recruiter(**kwargs):
        idx = next(_email_seq)
        email = kwargs.pop("email", f"recruiter{idx}@example.com")
        password = kwargs.pop("password", "Secure!Pass12345")
        defaults = {
            "is_verified_recruiter": True,
            "is_active": True,
        }
        defaults.update(kwargs)
        return django_user_model.objects.create_user(email=email, password=password, **defaults)

    return make_recruiter


@pytest.fixture
def staff_user(recruiter_factory):
    return recruiter_factory(is_staff=True, is_verified_recruiter=True)


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(email="admin@example.com", password="Secure!Pass12345")


@pytest.fixture
def candidate_factory():
    def make_candidate(**kwargs):
        idx = next(_candidate_seq)
        defaults = {
            "first_name": f"Clara{idx}",
            "last_name": "Mueller",
            "gender": CandidateGender.FEMALE,
            "country": "Germany",
            "region": "Berlin",
            "city": "Berlin",
            "hair_color": HairColor.BLONDE,
            "primary_email": f"clara{idx}@example.com",
            "primary_phone": f"+49151123{idx:04d}",
        }
        defaults.update(kwargs)
        return Candidate.objects.create(**defaults)

    return make_candidate


@pytest.fixture
def attribute_factory():
    def make_attribute(**kwargs):
        code = kwargs.pop("code", next(_attribute_seq))
        defaults = {
            "slug": f"attr-{code}",
            "label": f"Attribute {code}",
            "icon": "*",
            "is_active": True,
        }
        defaults.update(kwargs)
        return CandidateAttributeDefinition.objects.create(code=code, **defaults)

    return make_attribute


@pytest.fixture
def lookup_session_factory(candidate_factory):
    def make_lookup_session(**kwargs):
        candidate = kwargs.pop("candidate", None) or candidate_factory()
        defaults = {
            "requester": None,
            "requester_ip": "127.0.0.1",
            "initial_country": candidate.country,
            "initial_region": candidate.region,
            "initial_first_name": candidate.first_name,
            "initial_gender": candidate.gender,
            "candidate_ids": [candidate.id],
            "step_expires_at": timezone.now() + timedelta(minutes=5),
            "status": LookupSession.Status.ACTIVE,
        }
        defaults.update(kwargs)
        return LookupSession.objects.create(**defaults)

    return make_lookup_session


@pytest.fixture
def node_instance_factory():
    def make_node(**kwargs):
        idx = next(_node_seq)
        defaults = {
            "name": f"node-{idx}",
            "base_url": f"https://node-{idx}.example.com",
            "role": NodeInstance.Role.REPLICA,
            "status": NodeInstance.Status.ONLINE,
            "is_approved": True,
        }
        defaults.update(kwargs)
        return NodeInstance.objects.create(**defaults)

    return make_node


@pytest.fixture
def ip_ban_factory():
    def make_ban(**kwargs):
        defaults = {
            "ip": "127.0.0.2",
            "reason": "test",
            "strike_count": 1,
            "banned_until": timezone.now() + timedelta(minutes=30),
        }
        defaults.update(kwargs)
        return IPBan.objects.create(**defaults)

    return make_ban


@pytest.fixture
def captcha_challenge_factory():
    def make_captcha(*, code: str = "ABC123", **kwargs):
        salt = kwargs.pop("salt", "salt1234")
        defaults = {
            "code_digest": _digest(code, salt),
            "salt": salt,
            "attempts": 0,
            "max_attempts": 5,
            "expires_at": timezone.now() + timedelta(minutes=5),
        }
        defaults.update(kwargs)
        return CaptchaChallenge.objects.create(**defaults)

    return make_captcha


@pytest.fixture
def make_js_gate_headers():
    def build_headers(*, ip: str = "127.0.0.1", ua: str = "pytest-agent/1.0"):
        token = create_js_gate_token(ip=ip, user_agent=ua)
        return {
            "HTTP_X_JS_GATE": token,
            "HTTP_USER_AGENT": ua,
            "REMOTE_ADDR": ip,
        }

    return build_headers


@pytest.fixture
def js_gate_headers(make_js_gate_headers):
    return make_js_gate_headers()


@pytest.fixture
def auth_client(recruiter_factory):
    user = recruiter_factory()
    client = Client()
    client.force_login(user)
    return client, user


@pytest.fixture
def staff_client(staff_user):
    client = Client()
    client.force_login(staff_user)
    return client

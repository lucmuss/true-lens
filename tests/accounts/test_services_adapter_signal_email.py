from __future__ import annotations

import builtins
import types

import pytest
from allauth.account.adapter import DefaultAccountAdapter
from django.core.mail import EmailMultiAlternatives
from django.test import RequestFactory, override_settings

from apps.accounts.adapters import RecruiterAccountAdapter
from apps.accounts.email_backends import ResendEmailBackend
from apps.accounts.models import RecruiterSecurityVerification
from apps.accounts.services import send_login_alert
from apps.accounts.signals import login_alert_handler


@pytest.mark.django_db
def test_adapter_send_security_challenge_creates_verification_and_mail(recruiter_factory, monkeypatch):
    user = recruiter_factory()
    adapter = RecruiterAccountAdapter()
    request = RequestFactory().get("/")

    sent = []
    monkeypatch.setattr("apps.accounts.adapters.send_mail", lambda **kwargs: sent.append(kwargs))

    adapter._send_security_challenge(user, request)

    assert RecruiterSecurityVerification.objects.filter(recruiter=user).count() == 1
    assert len(sent) == 1


@pytest.mark.django_db
def test_adapter_save_user_sets_display_name_and_sends_challenge(django_user_model, monkeypatch):
    adapter = RecruiterAccountAdapter()
    request = RequestFactory().post("/accounts/signup/")

    user = django_user_model(email="newuser@example.com", is_verified_recruiter=False)

    monkeypatch.setattr(DefaultAccountAdapter, "save_user", lambda self, req, usr, form, commit=False: usr)

    sent = []
    monkeypatch.setattr(adapter, "_send_security_challenge", lambda usr, req: sent.append((usr.email, req.path)))

    returned = adapter.save_user(request, user, form=object(), commit=True)

    assert returned.display_name == "newuser"
    assert sent == [("newuser@example.com", "/accounts/signup/")]


@pytest.mark.django_db
def test_send_login_alert_skips_when_notification_disabled(recruiter_factory, monkeypatch):
    user = recruiter_factory(notify_on_security=False)
    called = []
    monkeypatch.setattr("apps.accounts.services.send_templated_email", lambda **kwargs: called.append(kwargs))

    send_login_alert(user=user, ip="127.0.0.1", user_agent="ua", app_public_url="https://example.com")

    assert called == []


@pytest.mark.django_db
def test_send_login_alert_calls_template_sender(recruiter_factory, monkeypatch):
    user = recruiter_factory(email="alert@example.com", notify_on_security=True)
    called = []
    monkeypatch.setattr("apps.accounts.services.send_templated_email", lambda **kwargs: called.append(kwargs))

    send_login_alert(user=user, ip="127.0.0.1", user_agent="ua", app_public_url="https://example.com")

    assert len(called) == 1
    assert called[0]["to"] == ["alert@example.com"]


@pytest.mark.django_db
def test_login_alert_handler_ignores_missing_request(recruiter_factory, monkeypatch):
    user = recruiter_factory()
    called = []
    monkeypatch.setattr("apps.accounts.signals.send_login_alert", lambda **kwargs: called.append(kwargs))

    login_alert_handler(sender=None, request=None, user=user)

    assert called == []


@pytest.mark.django_db
def test_login_alert_handler_calls_service(recruiter_factory, monkeypatch):
    user = recruiter_factory()
    request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="9.9.9.9", HTTP_USER_AGENT="pytest")
    called = []
    monkeypatch.setattr("apps.accounts.signals.send_login_alert", lambda **kwargs: called.append(kwargs))

    login_alert_handler(sender=None, request=request, user=user)

    assert len(called) == 1
    assert called[0]["ip"] == "9.9.9.9"


@pytest.mark.django_db
@override_settings(RESEND_API_KEY="")
def test_resend_backend_returns_zero_without_api_key():
    backend = ResendEmailBackend()
    assert backend.send_messages([]) == 0


@pytest.mark.django_db
@override_settings(RESEND_API_KEY="abc123", RESEND_FROM_EMAIL="from@example.com")
def test_resend_backend_handles_import_error(monkeypatch):
    backend = ResendEmailBackend()

    original_import = builtins.__import__

    def _import(name, *args, **kwargs):
        if name == "resend":
            raise ImportError("no resend")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _import)

    assert backend.send_messages([]) == 0


@pytest.mark.django_db
@override_settings(RESEND_API_KEY="abc123", RESEND_FROM_EMAIL="from@example.com")
def test_resend_backend_sends_messages(monkeypatch):
    backend = ResendEmailBackend()
    sent_calls = []
    original_import = builtins.__import__

    fake_module = types.SimpleNamespace(
        api_key=None,
        Emails=types.SimpleNamespace(send=lambda payload: sent_calls.append(payload)),
    )

    monkeypatch.setattr(
        builtins,
        "__import__",
        lambda name, *args, **kwargs: fake_module if name == "resend" else original_import(name, *args, **kwargs),
    )

    msg = EmailMultiAlternatives(subject="sub", body="body", to=["a@example.com", "b@example.com"])
    msg.attach_alternative("<b>body</b>", "text/html")

    count = backend.send_messages([msg])

    assert count == 2
    assert len(sent_calls) == 2


@pytest.mark.django_db
def test_send_templated_email_uses_html_alternative(monkeypatch):
    from apps.accounts.emails import send_templated_email

    sent = []

    class DummyMessage:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.alternatives = []

        def attach_alternative(self, html, content_type):
            self.alternatives.append((html, content_type))

        def send(self, fail_silently=True):
            sent.append((self.kwargs, self.alternatives, fail_silently))

    monkeypatch.setattr("apps.accounts.emails.EmailMultiAlternatives", lambda **kwargs: DummyMessage(**kwargs))
    monkeypatch.setattr("apps.accounts.emails.render_to_string", lambda template, context: f"{template}:{context['name']}")

    send_templated_email(
        to=["x@example.com"],
        subject="Subject",
        text_template="emails/a.txt",
        html_template="emails/a.html",
        context={"name": "N"},
    )

    assert len(sent) == 1
    assert sent[0][0]["subject"] == "Subject"
    assert sent[0][1][0][1] == "text/html"

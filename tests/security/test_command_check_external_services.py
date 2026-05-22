from __future__ import annotations

import io

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.security.management.commands.check_external_services import CheckResult, Command


@override_settings(EXTERNAL_SERVICES_CHECK_STRICT="false", EXTERNAL_SERVICES_CHECK_TIMEOUT=2)
def test_check_external_services_non_strict_logs_failures_and_continues(monkeypatch):
    monkeypatch.setattr(Command, "_check_stripe", lambda self, timeout: CheckResult("Stripe", False, "network error"))
    monkeypatch.setattr(Command, "_check_resend", lambda self, timeout: CheckResult("Resend", True, "SKIP (mode not active)"))
    monkeypatch.setattr(Command, "_check_smtp", lambda self, timeout: CheckResult("SMTP", True, "OK"))
    monkeypatch.setattr(Command, "_check_sentry", lambda self, timeout: CheckResult("Sentry", True, "OK"))

    out = io.StringIO()
    call_command("check_external_services", stdout=out)

    output = out.getvalue()
    assert "[FAIL] Stripe: network error" in output
    assert "[SKIP] Resend: SKIP (mode not active)" in output
    assert "[OK] SMTP: OK" in output


@override_settings(EXTERNAL_SERVICES_CHECK_STRICT="true", EXTERNAL_SERVICES_CHECK_TIMEOUT=2)
def test_check_external_services_strict_mode_exits_on_failure(monkeypatch):
    monkeypatch.setattr(Command, "_check_stripe", lambda self, timeout: CheckResult("Stripe", False, "network error"))
    monkeypatch.setattr(Command, "_check_resend", lambda self, timeout: CheckResult("Resend", True, "OK"))
    monkeypatch.setattr(Command, "_check_smtp", lambda self, timeout: CheckResult("SMTP", True, "OK"))
    monkeypatch.setattr(Command, "_check_sentry", lambda self, timeout: CheckResult("Sentry", True, "OK"))

    with pytest.raises(SystemExit) as exc:
        call_command("check_external_services", stdout=io.StringIO())

    assert exc.value.code == 1


@override_settings(EMAIL_DELIVERY_MODE="smtp", EMAIL_HOST="", EMAIL_PORT=587, EMAIL_USE_TLS=True)
def test_check_external_services_smtp_check_requires_host():
    result = Command()._check_smtp(timeout=1)

    assert result.name == "SMTP"
    assert result.ok is False
    assert "EMAIL_HOST missing" in result.message


@override_settings(EMAIL_DELIVERY_MODE="resend", USE_RESEND=True, RESEND_API_KEY="")
def test_check_external_services_resend_check_requires_api_key():
    result = Command()._check_resend(timeout=1)

    assert result.name == "Resend"
    assert result.ok is False
    assert "RESEND_API_KEY missing" in result.message


@override_settings(SENTRY_DSN="invalid-dsn")
def test_check_external_services_sentry_check_validates_dsn_format():
    result = Command()._check_sentry(timeout=1)

    assert result.name == "Sentry"
    assert result.ok is False
    assert "invalid DSN format" in result.message

from __future__ import annotations

import smtplib
import socket
from dataclasses import dataclass

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str


class Command(BaseCommand):
    help = "Checks configured external providers before startup"

    def handle(self, *args, **options):
        strict = str(getattr(settings, "EXTERNAL_SERVICES_CHECK_STRICT", "")).lower() in {"1", "true", "yes", "on"}
        timeout = int(getattr(settings, "EXTERNAL_SERVICES_CHECK_TIMEOUT", 10) or 10)
        results = [
            self._check_stripe(timeout),
            self._check_resend(timeout),
            self._check_smtp(timeout),
            self._check_sentry(timeout),
        ]

        has_fail = False
        for result in results:
            status = "OK" if result.ok else "FAIL"
            if result.message.startswith("SKIP"):
                status = "SKIP"
            self.stdout.write(f"[{status}] {result.name}: {result.message}")
            if status == "FAIL":
                has_fail = True

        if has_fail and strict:
            raise SystemExit(1)

    def _check_stripe(self, timeout: int) -> CheckResult:
        key = (settings.STRIPE_SECRET_KEY or "").strip()
        if not key:
            return CheckResult("Stripe", True, "SKIP (not configured)")
        try:
            response = requests.get(
                "https://api.stripe.com/v1/charges?limit=1",
                auth=(key, ""),
                timeout=timeout,
                headers={"User-Agent": "truelens-preflight/1.0"},
            )
        except requests.RequestException as exc:
            return CheckResult("Stripe", False, f"network error: {exc}")
        if response.status_code in {200, 401}:
            return CheckResult("Stripe", True, "OK")
        return CheckResult("Stripe", False, f"unexpected status {response.status_code}")

    def _check_resend(self, timeout: int) -> CheckResult:
        if settings.EMAIL_DELIVERY_MODE != "resend" and not getattr(settings, "USE_RESEND", False):
            return CheckResult("Resend", True, "SKIP (mode not active)")
        key = (settings.RESEND_API_KEY or "").strip()
        if not key:
            return CheckResult("Resend", False, "RESEND_API_KEY missing")
        try:
            response = requests.get(
                "https://api.resend.com/domains",
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Accept": "application/json",
                    "User-Agent": "truelens-preflight/1.0",
                },
            )
        except requests.RequestException as exc:
            return CheckResult("Resend", False, f"network error: {exc}")
        if response.status_code in {200, 401, 403}:
            return CheckResult("Resend", True, f"OK (HTTP {response.status_code})")
        return CheckResult("Resend", False, f"unexpected status {response.status_code}")

    def _check_smtp(self, timeout: int) -> CheckResult:
        if settings.EMAIL_DELIVERY_MODE != "smtp":
            return CheckResult("SMTP", True, f"SKIP (EMAIL_DELIVERY_MODE={settings.EMAIL_DELIVERY_MODE})")
        host = (settings.EMAIL_HOST or "").strip()
        if not host:
            return CheckResult("SMTP", False, "EMAIL_HOST missing")
        port = int(settings.EMAIL_PORT or 587)
        try:
            conn = smtplib.SMTP(host=host, port=port, timeout=timeout)
            if settings.EMAIL_USE_TLS:
                conn.starttls()
            if settings.EMAIL_HOST_USER:
                conn.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            conn.quit()
            return CheckResult("SMTP", True, "OK")
        except (OSError, smtplib.SMTPException, TimeoutError) as exc:
            return CheckResult("SMTP", False, f"smtp error: {exc}")

    def _check_sentry(self, timeout: int) -> CheckResult:
        dsn = (settings.SENTRY_DSN or "").strip()
        if not dsn:
            return CheckResult("Sentry", True, "SKIP (not configured)")
        try:
            host = dsn.split("@", 1)[1].split("/", 1)[0]
        except IndexError:
            return CheckResult("Sentry", False, "invalid DSN format")
        try:
            socket.create_connection((host, 443), timeout=timeout).close()
            return CheckResult("Sentry", True, "OK")
        except OSError as exc:
            return CheckResult("Sentry", False, f"network error: {exc}")

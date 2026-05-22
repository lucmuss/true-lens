from __future__ import annotations

import json

import pytest
from django.test import override_settings

from apps.credits.models import CreditLedgerEntry


@pytest.mark.django_db
def test_credit_checkout_requires_auth(client, js_gate_headers):
    response = client.post(
        "/api/credits/checkout",
        data=json.dumps({"quantity": 1}),
        content_type="application/json",
        **js_gate_headers,
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_credit_checkout_rejects_invalid_quantity(client, recruiter_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)

    response = client.post(
        "/api/credits/checkout",
        data=json.dumps({"quantity": 0}),
        content_type="application/json",
        **js_gate_headers,
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_credit_checkout_requires_stripe_config(client, recruiter_factory, js_gate_headers):
    user = recruiter_factory()
    client.force_login(user)

    with override_settings(STRIPE_SECRET_KEY=""):
        response = client.post(
            "/api/credits/checkout",
            data=json.dumps({"quantity": 2}),
            content_type="application/json",
            **js_gate_headers,
        )

    assert response.status_code == 503


@pytest.mark.django_db
def test_credit_checkout_success_returns_url(client, recruiter_factory, js_gate_headers, monkeypatch):
    user = recruiter_factory()
    client.force_login(user)

    monkeypatch.setattr("apps.credits.api_views.create_checkout_session", lambda **kwargs: "https://checkout.test")

    with override_settings(STRIPE_SECRET_KEY="sk_test"):
        response = client.post(
            "/api/credits/checkout",
            data=json.dumps({"quantity": 3}),
            content_type="application/json",
            **js_gate_headers,
        )

    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://checkout.test"


@pytest.mark.django_db
def test_stripe_webhook_unconfigured_returns_503(client):
    with override_settings(STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET=""):
        response = client.post("/api/credits/webhook/stripe", data=b"{}", content_type="application/json")
    assert response.status_code == 503


@pytest.mark.django_db
def test_stripe_webhook_invalid_payload_returns_400(client, monkeypatch):
    class _Webhook:
        @staticmethod
        def construct_event(**kwargs):
            raise ValueError("bad")

    monkeypatch.setattr("apps.credits.api_views.stripe.Webhook", _Webhook)

    with override_settings(STRIPE_SECRET_KEY="sk_test", STRIPE_WEBHOOK_SECRET="whsec"):
        response = client.post("/api/credits/webhook/stripe", data=b"{}", content_type="application/json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_stripe_webhook_invalid_signature_returns_400(client, monkeypatch):
    class _Webhook:
        @staticmethod
        def construct_event(**kwargs):
            import stripe

            raise stripe.error.SignatureVerificationError("bad", "sig")

    monkeypatch.setattr("apps.credits.api_views.stripe.Webhook", _Webhook)

    with override_settings(STRIPE_SECRET_KEY="sk_test", STRIPE_WEBHOOK_SECRET="whsec"):
        response = client.post("/api/credits/webhook/stripe", data=b"{}", content_type="application/json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_wallet_requires_auth(client, js_gate_headers):
    response = client.get("/api/credits/wallet", **js_gate_headers)
    assert response.status_code == 302


@pytest.mark.django_db
def test_wallet_returns_credits_and_ledger(client, recruiter_factory, js_gate_headers):
    user = recruiter_factory(credits=5)
    client.force_login(user)
    CreditLedgerEntry.objects.create(recruiter=user, entry_type=CreditLedgerEntry.EntryType.PURCHASE, delta=2)

    response = client.get("/api/credits/wallet", **js_gate_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["credits"] == 5
    assert len(payload["ledger"]) >= 1

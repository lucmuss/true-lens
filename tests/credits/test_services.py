from __future__ import annotations

import types

import pytest
from django.test import override_settings

from apps.credits.models import CreditLedgerEntry, CreditPurchase
from apps.credits.services import _credit_unit_price, create_checkout_session, handle_checkout_completed


@pytest.mark.django_db
@override_settings(CREDIT_PRICE_EUR="1.25")
def test_credit_unit_price_from_settings():
    assert str(_credit_unit_price()) == "1.25"


@pytest.mark.django_db
@override_settings(CREDIT_PRICE_EUR="bad")
def test_credit_unit_price_invalid_raises():
    with pytest.raises(Exception):
        _credit_unit_price()


@pytest.mark.django_db
@override_settings(STRIPE_SECRET_KEY="sk_test", STRIPE_DEFAULT_CURRENCY="eur", CREDIT_PRICE_EUR="1.00")
def test_create_checkout_session_persists_purchase(recruiter_factory, monkeypatch):
    recruiter = recruiter_factory()

    fake_session = types.SimpleNamespace(id="cs_test_1", url="https://stripe.test/checkout")
    monkeypatch.setattr(
        "apps.credits.services.stripe.checkout.Session.create",
        lambda **kwargs: fake_session,
    )

    url = create_checkout_session(
        recruiter=recruiter,
        quantity=3,
        success_url="https://ok",
        cancel_url="https://cancel",
    )

    assert url == "https://stripe.test/checkout"
    purchase = CreditPurchase.objects.get(stripe_session_id="cs_test_1")
    assert purchase.credits_purchased == 3
    assert purchase.status == CreditPurchase.Status.PENDING


@pytest.mark.django_db
def test_handle_checkout_completed_returns_false_without_id():
    assert handle_checkout_completed({}) is False


@pytest.mark.django_db
def test_handle_checkout_completed_returns_false_for_unknown_session():
    assert handle_checkout_completed({"id": "missing"}) is False


@pytest.mark.django_db
def test_handle_checkout_completed_is_idempotent(recruiter_factory):
    recruiter = recruiter_factory(credits=0)
    purchase = CreditPurchase.objects.create(
        recruiter=recruiter,
        credits_purchased=2,
        amount_paid="2.00",
        stripe_session_id="cs_test_2",
        status=CreditPurchase.Status.PENDING,
    )

    assert handle_checkout_completed({"id": "cs_test_2", "payment_intent": "pi_1"}) is True
    recruiter.refresh_from_db()
    assert recruiter.credits == 2
    assert CreditLedgerEntry.objects.filter(recruiter=recruiter, entry_type=CreditLedgerEntry.EntryType.PURCHASE).count() == 1

    assert handle_checkout_completed({"id": "cs_test_2", "payment_intent": "pi_1"}) is True
    recruiter.refresh_from_db()
    assert recruiter.credits == 2
    assert CreditLedgerEntry.objects.filter(recruiter=recruiter, entry_type=CreditLedgerEntry.EntryType.PURCHASE).count() == 1

    purchase.refresh_from_db()
    assert purchase.status == CreditPurchase.Status.COMPLETED

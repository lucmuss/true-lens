from __future__ import annotations

from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction

from .models import CreditLedgerEntry, CreditPurchase


def _credit_unit_price() -> Decimal:
    raw = getattr(settings, "CREDIT_PRICE_EUR", None) or "1.00"
    return Decimal(str(raw))


def create_checkout_session(*, recruiter, quantity: int, success_url: str, cancel_url: str) -> str:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    unit = _credit_unit_price()

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": settings.STRIPE_DEFAULT_CURRENCY,
                    "product_data": {"name": "Recruiter Credits"},
                    "unit_amount": int(unit * 100),
                },
                "quantity": quantity,
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"recruiter_id": str(recruiter.id), "credits": str(quantity)},
    )

    CreditPurchase.objects.create(
        recruiter=recruiter,
        credits_purchased=quantity,
        amount_paid=unit * quantity,
        stripe_session_id=session.id,
        status=CreditPurchase.Status.PENDING,
    )
    return session.url


@transaction.atomic
def handle_checkout_completed(session_obj: dict) -> bool:
    session_id = str(session_obj.get("id") or "")
    if not session_id:
        return False

    purchase = CreditPurchase.objects.select_for_update().filter(stripe_session_id=session_id).first()
    if purchase is None:
        return False
    if purchase.status == CreditPurchase.Status.COMPLETED:
        return True

    purchase.stripe_payment_intent_id = str(session_obj.get("payment_intent") or "")
    purchase.complete()

    recruiter = purchase.recruiter
    recruiter.add_credits(purchase.credits_purchased, save=True)
    CreditLedgerEntry.objects.create(
        recruiter=recruiter,
        entry_type=CreditLedgerEntry.EntryType.PURCHASE,
        delta=purchase.credits_purchased,
        reason=f"Stripe session {purchase.stripe_session_id}",
    )
    return True

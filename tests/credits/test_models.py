from __future__ import annotations

import pytest

from apps.credits.models import CreditPurchase


@pytest.mark.django_db
def test_credit_purchase_complete_sets_status_and_timestamp(recruiter_factory):
    purchase = CreditPurchase.objects.create(
        recruiter=recruiter_factory(),
        credits_purchased=2,
        amount_paid="2.00",
        stripe_session_id="sess-1",
    )

    purchase.complete()
    purchase.refresh_from_db()
    assert purchase.status == CreditPurchase.Status.COMPLETED
    assert purchase.completed_at is not None


@pytest.mark.django_db
def test_credit_purchase_complete_is_idempotent(recruiter_factory):
    purchase = CreditPurchase.objects.create(
        recruiter=recruiter_factory(),
        credits_purchased=1,
        amount_paid="1.00",
        stripe_session_id="sess-2",
    )

    purchase.complete()
    first_completed_at = purchase.completed_at
    purchase.complete()
    purchase.refresh_from_db()

    assert purchase.completed_at == first_completed_at

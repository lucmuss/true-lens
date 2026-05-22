from __future__ import annotations

import json

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import CreditLedgerEntry
from .services import create_checkout_session, handle_checkout_completed


def _body(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


@require_POST
@login_required
def credit_checkout(request):
    payload = _body(request)
    quantity_raw = payload.get("quantity", 1)
    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Invalid quantity"}, status=400)

    if quantity < 1 or quantity > 100:
        return JsonResponse({"ok": False, "error": "Quantity must be between 1 and 100"}, status=400)
    if not settings.STRIPE_SECRET_KEY:
        return JsonResponse({"ok": False, "error": "Stripe is not configured"}, status=503)

    success_url = request.build_absolute_uri(reverse("dashboard")) + "?checkout=success"
    cancel_url = request.build_absolute_uri(reverse("dashboard")) + "?checkout=cancel"

    try:
        checkout_url = create_checkout_session(
            recruiter=request.user,
            quantity=quantity,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except stripe.error.StripeError as exc:
        return JsonResponse({"ok": False, "error": f"Stripe error: {exc.user_message or str(exc)}"}, status=502)

    return JsonResponse({"ok": True, "checkout_url": checkout_url})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        return JsonResponse({"ok": False, "error": "Stripe webhook not configured"}, status=503)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({"ok": False, "error": "Invalid signature"}, status=400)

    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})

    if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        handle_checkout_completed(obj)

    return JsonResponse({"ok": True})


@require_GET
@login_required
def wallet(request):
    ledger = list(
        CreditLedgerEntry.objects.filter(recruiter=request.user)
        .values("entry_type", "delta", "reason", "created_at")
        .order_by("-created_at")[:30]
    )
    return JsonResponse({"ok": True, "credits": request.user.credits, "ledger": ledger})

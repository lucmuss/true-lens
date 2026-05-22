from __future__ import annotations

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.candidates.models import Candidate

from .models import RecruiterContactRelay, RecruiterUser


def _body(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


@require_POST
@login_required
def create_contact_request(request):
    payload = _body(request)
    candidate_id = int(payload.get("candidate_id") or 0)
    target_email = str(payload.get("target_email") or "").strip().lower()
    message = str(payload.get("message") or "").strip()

    if not candidate_id or not target_email:
        return JsonResponse({"ok": False, "error": "candidate_id and target_email are required"}, status=400)

    candidate = Candidate.objects.filter(id=candidate_id).first()
    if candidate is None:
        return JsonResponse({"ok": False, "error": "Candidate not found"}, status=404)

    target = RecruiterUser.objects.filter(email=target_email, is_active=True).first()
    if target is None:
        return JsonResponse({"ok": False, "error": "Target recruiter not found"}, status=404)
    if target == request.user:
        return JsonResponse({"ok": False, "error": "Cannot contact yourself"}, status=400)

    relay = RecruiterContactRelay.objects.create(
        initiator=request.user,
        target=target,
        candidate_id=candidate.id,
        message=message,
    )

    send_mail(
        subject=f"{settings.PROJECT_NAME}: Kontaktanfrage zu gemeinsamem Profil",
        message=(
            "Eine Recruiter-Kontaktanfrage wurde fuer Kandidat "
            f"{candidate.first_name} {candidate.masked_last_name} erstellt.\n"
            f"Bitte pruefe im Dashboard und akzeptiere oder lehne ab."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[target.email],
        fail_silently=True,
    )

    return JsonResponse({"ok": True, "relay_id": relay.id})


@require_POST
@login_required
def accept_contact_request(request, relay_id: int):
    relay = RecruiterContactRelay.objects.filter(id=relay_id, target=request.user).first()
    if relay is None:
        return JsonResponse({"ok": False, "error": "Relay request not found"}, status=404)
    if relay.status != RecruiterContactRelay.Status.PENDING:
        return JsonResponse({"ok": False, "error": "Relay request already handled"}, status=400)

    candidate = Candidate.objects.filter(id=relay.candidate_id).first()
    candidate_name = (
        f"{candidate.first_name} {candidate.masked_last_name}" if candidate else f"Candidate #{relay.candidate_id}"
    )

    relay.status = RecruiterContactRelay.Status.ACCEPTED
    relay.resolved_at = timezone.now()
    relay.save(update_fields=["status", "resolved_at"])

    send_mail(
        subject=f"{settings.PROJECT_NAME}: Kontaktfreigabe fuer Recruiter",
        message=(
            f"Kontakt wurde freigegeben fuer {candidate_name}.\n"
            f"Initiator: {relay.initiator.email}\n"
            f"Ziel: {relay.target.email}\n"
            "Ihr koennt euch jetzt direkt austauschen."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[relay.initiator.email, relay.target.email],
        fail_silently=True,
    )

    return JsonResponse({"ok": True})


@require_POST
@login_required
def reject_contact_request(request, relay_id: int):
    relay = RecruiterContactRelay.objects.filter(id=relay_id, target=request.user).first()
    if relay is None:
        return JsonResponse({"ok": False, "error": "Relay request not found"}, status=404)
    if relay.status != RecruiterContactRelay.Status.PENDING:
        return JsonResponse({"ok": False, "error": "Relay request already handled"}, status=400)

    relay.status = RecruiterContactRelay.Status.REJECTED
    relay.resolved_at = timezone.now()
    relay.save(update_fields=["status", "resolved_at"])
    return JsonResponse({"ok": True})

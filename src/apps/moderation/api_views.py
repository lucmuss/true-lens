from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import DataEnrichmentSubmission


@require_GET
@staff_member_required
def queue_list(request):
    rows = list(
        DataEnrichmentSubmission.objects.filter(status=DataEnrichmentSubmission.Status.PENDING)
        .select_related("candidate", "recruiter")
        .values(
            "id",
            "candidate_id",
            "candidate__first_name",
            "candidate__last_name",
            "recruiter__email",
            "payload",
            "created_at",
        )
        .order_by("created_at")[:100]
    )
    return JsonResponse({"ok": True, "items": rows})


@require_POST
@staff_member_required
def queue_approve(request, item_id: int):
    item = DataEnrichmentSubmission.objects.filter(id=item_id).select_related("candidate").first()
    if item is None:
        return JsonResponse({"ok": False, "error": "Item not found"}, status=404)
    if item.status != DataEnrichmentSubmission.Status.PENDING:
        return JsonResponse({"ok": False, "error": "Item already reviewed"}, status=400)

    editable_fields = {
        "secondary_email",
        "secondary_phone",
        "hair_color",
        "country",
        "region",
        "city",
        "dating_profile_url",
    }
    candidate = item.candidate
    for key, value in item.payload.items():
        if key in editable_fields:
            setattr(candidate, key, value)
    candidate.save()

    item.status = DataEnrichmentSubmission.Status.APPROVED
    item.reviewed_at = timezone.now()
    item.save(update_fields=["status", "reviewed_at"])

    return JsonResponse({"ok": True})


@require_POST
@staff_member_required
def queue_reject(request, item_id: int):
    item = DataEnrichmentSubmission.objects.filter(id=item_id).first()
    if item is None:
        return JsonResponse({"ok": False, "error": "Item not found"}, status=404)
    if item.status != DataEnrichmentSubmission.Status.PENDING:
        return JsonResponse({"ok": False, "error": "Item already reviewed"}, status=400)

    item.status = DataEnrichmentSubmission.Status.REJECTED
    item.reviewed_at = timezone.now()
    item.save(update_fields=["status", "reviewed_at"])

    return JsonResponse({"ok": True})

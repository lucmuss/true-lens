from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models as db_models
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.accounts.models import RecruiterContactRelay
from apps.candidates.models import Candidate, CandidateAttributeDefinition, CandidateAttributeVote, HairColor
from apps.credits.models import CreditLedgerEntry, CreditPurchase
from apps.moderation.models import DataEnrichmentSubmission, SupporterNodeApplication
from apps.replication.models import NodeInstance
from apps.security.models import IPBan


@staff_member_required
def admin_dashboard(request):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    now = timezone.now()

    credits_sold = CreditLedgerEntry.objects.filter(
        entry_type=CreditLedgerEntry.EntryType.PURCHASE
    ).aggregate(total=Sum("delta"))["total"] or 0

    revenue = CreditPurchase.objects.filter(
        status=CreditPurchase.Status.COMPLETED
    ).aggregate(total=Sum("amount_paid"))["total"] or 0

    credits_outstanding = User.objects.filter(is_active=True).aggregate(
        total=Sum("credits")
    )["total"] or 0

    stats = {
        "candidate_count": Candidate.objects.count(),
        "recruiter_count": User.objects.filter(is_active=True).count(),
        "total_votes": CandidateAttributeVote.objects.count(),
        "total_views": Candidate.objects.aggregate(v=Sum("profile_views_count"))["v"] or 0,
        "credits_sold": credits_sold,
        "revenue_eur": f"{revenue:.2f}",
        "credits_outstanding": credits_outstanding,
    }

    return render(
        request,
        "admin_dashboard.html",
        {
            "stats": stats,
            "nodes": NodeInstance.objects.order_by("role", "name"),
            "pending_enrichments": DataEnrichmentSubmission.objects.filter(
                status=DataEnrichmentSubmission.Status.PENDING
            ).select_related("candidate", "recruiter").order_by("-created_at")[:50],
            "pending_node_apps": SupporterNodeApplication.objects.filter(
                status=SupporterNodeApplication.Status.PENDING
            ).order_by("-created_at")[:50],
            "active_bans": IPBan.objects.filter(banned_until__gt=now).order_by("-strike_count")[:50],
        },
    )


def landing(request):
    candidate_count = Candidate.objects.count()
    profile_views = Candidate.objects.aggregate(total=Count("view_logs")).get("total", 0)
    return render(
        request,
        "landing.html",
        {
            "candidate_count": candidate_count,
            "profile_views": profile_views,
        },
    )


@login_required
def dashboard(request):
    recent_votes = (
        CandidateAttributeVote.objects.filter(recruiter=request.user)
        .select_related("candidate", "attribute")
        .order_by("-voted_on")[:30]
    )
    attributes = list(CandidateAttributeDefinition.objects.filter(is_active=True).order_by("code"))
    pending_relays_incoming = (
        RecruiterContactRelay.objects.filter(
            target=request.user,
            status=RecruiterContactRelay.Status.PENDING,
        )
        .select_related("initiator")
        .order_by("-created_at")[:20]
    )
    pending_relays_outgoing = (
        RecruiterContactRelay.objects.filter(
            initiator=request.user,
            status=RecruiterContactRelay.Status.PENDING,
        )
        .select_related("target")
        .order_by("-created_at")[:20]
    )
    return render(
        request,
        "dashboard.html",
        {
            "recent_votes": recent_votes,
            "attributes": attributes,
            "hair_colors": list(HairColor.choices),
            "pending_relays_incoming": pending_relays_incoming,
            "pending_relays_outgoing": pending_relays_outgoing,
        },
    )


@login_required
def vote_history(request):
    qs = (
        CandidateAttributeVote.objects.filter(recruiter=request.user)
        .select_related("candidate", "attribute")
        .order_by("-voted_on", "-id")
    )
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "vote_history.html", {"page_obj": page_obj})


def profile_page(request, candidate_id: int):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    grouped_votes = candidate.public_vote_breakdown()
    return render(
        request,
        "profile.html",
        {
            "candidate": candidate,
            "grouped_votes": grouped_votes,
            "hair_colors": list(HairColor.choices),
        },
    )

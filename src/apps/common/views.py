from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from apps.candidates.models import Candidate, CandidateAttributeDefinition, CandidateAttributeVote, HairColor


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
    return render(
        request,
        "dashboard.html",
        {
            "recent_votes": recent_votes,
            "attributes": attributes,
            "hair_colors": list(HairColor.choices),
        },
    )


def profile_page(request, candidate_id: int):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    grouped_votes = candidate.public_vote_breakdown()
    return render(
        request,
        "profile.html",
        {
            "candidate": candidate,
            "grouped_votes": grouped_votes,
        },
    )

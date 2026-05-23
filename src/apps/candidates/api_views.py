from __future__ import annotations

import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from apps.security.services import extract_client_ip

from .google_places import GooglePlacesError, autocomplete_cities
from .location_data import COUNTRY_TO_ISO2, REGIONS_BY_COUNTRY, country_suggestions
from .models import Candidate, LookupSession
from .services import (
    advance_lookup_session,
    cast_votes,
    create_candidate_record,
    create_lookup_session,
    reveal_profile,
    submit_candidate_enrichment,
)


def _body(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


@require_GET
def country_autocomplete(request):
    q = (request.GET.get("q") or "").strip()
    return JsonResponse({"suggestions": country_suggestions(q, limit=8)})


@require_GET
@login_required
def first_name_autocomplete(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"suggestions": []})
    names = (
        Candidate.objects.filter(first_name__istartswith=q)
        .values_list("first_name", flat=True)
        .distinct()
        .order_by("first_name")[:10]
    )
    return JsonResponse({"suggestions": list(names)})


@require_GET
def region_autocomplete(request):
    country = (request.GET.get("country") or "").strip()
    q = (request.GET.get("q") or "").strip().lower()
    regions = REGIONS_BY_COUNTRY.get(country, [])
    if q:
        regions = [r for r in regions if q in r.lower()]
    return JsonResponse({"suggestions": [{"label": r, "value": r} for r in regions[:30]]})


@require_GET
def city_autocomplete(request):
    q = (request.GET.get("q") or "").strip()
    country = (request.GET.get("country") or "").strip()
    region = (request.GET.get("region") or "").strip()
    if len(q) < 2:
        return JsonResponse({"suggestions": []})
    country_code = COUNTRY_TO_ISO2.get(country.lower().strip(), "")
    try:
        suggestions = autocomplete_cities(
            q,
            country_code=country_code,
            region=region,
            session_token=(request.GET.get("session_token") or "").strip(),
        )
    except GooglePlacesError as exc:
        return JsonResponse({"suggestions": [], "error": str(exc)}, status=503)

    return JsonResponse(
        {
            "suggestions": [
                {
                    "label": suggestion.text,
                    "value": suggestion.text.split(",", 1)[0].strip(),
                    "place_id": suggestion.place_id,
                }
                for suggestion in suggestions
            ]
        }
    )


@require_POST
def search_start(request):
    payload = _body(request)
    ip = extract_client_ip(request)
    ok, data = create_lookup_session(payload=payload, user=request.user, ip=ip)
    status = 200 if ok else 400
    return JsonResponse({"ok": ok, **data}, status=status)


@require_POST
def search_step(request, step: int):
    payload = _body(request)
    ip = extract_client_ip(request)
    token = (payload.get("session_token") or "").strip()
    payload["step"] = step
    ok, data = advance_lookup_session(token=token, payload=payload, ip=ip)
    status = 200 if ok else 400
    return JsonResponse({"ok": ok, **data}, status=status)


@require_GET
def search_status(request, token: str):
    ip = extract_client_ip(request)
    session = LookupSession.objects.filter(token=token, requester_ip=ip).first()
    if session is None:
        return JsonResponse({"ok": False, "error": "Session not found"}, status=404)

    now = datetime.now(tz=session.updated_at.tzinfo)
    ttl = max(0, int((session.step_expires_at - now).total_seconds())) if session.step_expires_at else 0
    return JsonResponse(
        {
            "ok": True,
            "status": session.status,
            "current_step": session.current_step,
            "case_type": session.case_type,
            "remaining_candidates": len(session.candidate_ids),
            "step_ttl_seconds": ttl,
        }
    )


@require_GET
def search_profile(request, token: str):
    ip = extract_client_ip(request)
    ok, data = reveal_profile(token=token, ip=ip, user=request.user)
    status = 200 if ok else 400
    return JsonResponse({"ok": ok, **data}, status=status)


@require_POST
@login_required
def candidate_vote(request, candidate_id: int):
    payload = _body(request)
    attr_codes = payload.get("attribute_codes") or []
    anonymous = bool(payload.get("anonymous"))

    try:
        codes = [int(code) for code in attr_codes]
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "attribute_codes must be integers"}, status=400)

    ok, data = cast_votes(candidate_id=candidate_id, recruiter=request.user, attribute_codes=codes, anonymous=anonymous)
    return JsonResponse({"ok": ok, **data}, status=200 if ok else 400)


@require_GET
def candidate_votes(request, candidate_id: int):
    candidate = Candidate.objects.filter(id=candidate_id).first()
    if candidate is None:
        return JsonResponse({"ok": False, "error": "Candidate not found"}, status=404)
    return JsonResponse({"ok": True, "votes": candidate.public_vote_breakdown()})


@require_POST
@login_required
def candidate_create(request):
    payload = _body(request)
    ok, data = create_candidate_record(payload=payload, recruiter=request.user)
    return JsonResponse({"ok": ok, **data}, status=200 if ok else 400)


@require_POST
@login_required
def candidate_enrichment(request, candidate_id: int):
    payload = _body(request)
    ok, data = submit_candidate_enrichment(candidate_id=candidate_id, payload=payload, recruiter=request.user)
    return JsonResponse({"ok": ok, **data}, status=200 if ok else 400)

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone

from apps.credits.models import CreditLedgerEntry
from apps.moderation.models import DataEnrichmentSubmission
from apps.security.services import register_security_failure

from .models import (
    Candidate,
    CandidateAttributeDefinition,
    CandidateAttributeVote,
    CandidateViewLog,
    HairColor,
    LookupAttempt,
    LookupSession,
    detect_social_platform,
    normalize_token,
)

CASE_PIPELINES: dict[str, list[str]] = {
    "birthdate": ["birth_date", "city", "hair_color"],
    "email": ["email", "city"],
    "phone": ["phone", "city"],
    "age": ["age", "city"],
    "social": ["social_url", "city", "age"],
    "lastname": ["last_name", "city"],
}


def load_default_attributes() -> None:
    path = Path(settings.CANDIDATE_ATTRIBUTE_CONFIG_PATH)
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    for item in data:
        CandidateAttributeDefinition.objects.update_or_create(
            code=int(item["code"]),
            defaults={
                "slug": item["slug"],
                "label": item["label"],
                "icon": item.get("icon", ""),
                "is_active": True,
            },
        )


def initial_candidate_queryset(*, country: str, region: str, first_name: str, gender: str):
    first_norm = normalize_token(first_name)
    if not first_norm:
        return Candidate.objects.none()

    base = Candidate.objects.filter(
        country__iexact=country.strip(),
        region__iexact=region.strip(),
        gender=gender,
    )
    # Prefix prefilter for performance then fuzzy in Python.
    quick = base.filter(first_name_norm__startswith=first_norm[:1])[:300]
    matched_ids = [candidate.id for candidate in quick if candidate.fuzzy_match_first_name(first_name)]
    return Candidate.objects.filter(id__in=matched_ids)


def _candidate_filter_for_case(case_type: str, candidates, value: Any):
    if case_type == "birthdate":
        return candidates.filter(birth_date=value)
    if case_type == "email":
        email = (value or "").strip().lower()
        return candidates.filter(models.Q(primary_email__iexact=email) | models.Q(secondary_email__iexact=email))
    if case_type == "phone":
        phone = (value or "").strip()
        return candidates.filter(models.Q(primary_phone=phone) | models.Q(secondary_phone=phone))
    if case_type == "age":
        try:
            age = int(value)
        except (TypeError, ValueError):
            return candidates.none()
        return candidates.filter(models.Q(age_years=age) | models.Q(birth_date__isnull=False))
    if case_type == "social":
        url = (value or "").strip()
        platform = detect_social_platform(url)
        if platform is None:
            return candidates.none()
        return candidates.filter(dating_profile_url__iexact=url, dating_platform=platform)
    if case_type == "lastname":
        value_norm = normalize_token(str(value))
        ids = [candidate.id for candidate in candidates if candidate.fuzzy_match_last_name(value_norm)]
        return candidates.filter(id__in=ids)
    return candidates.none()


def _city_filter(candidates, value: str):
    return candidates.filter(city__iexact=(value or "").strip())


def _hair_color_filter(candidates, value: str):
    if not value:
        return candidates.none()
    # Accept both integer value and label text.
    try:
        color_id = int(value)
        return candidates.filter(hair_color=color_id)
    except (TypeError, ValueError):
        label = str(value).strip().lower()
        mapping = {choice.label.lower(): int(choice.value) for choice in HairColor}
        if label in mapping:
            return candidates.filter(hair_color=mapping[label])
    return candidates.none()


def _age_filter(candidates, value: str):
    try:
        age = int(value)
    except (TypeError, ValueError):
        return candidates.none()
    return candidates.filter(age_years=age)


def _record_attempt(session: LookupSession, *, step: int, ip: str, success: bool, reason: str = "") -> None:
    LookupAttempt.objects.create(session=session, step=step, ip=ip, success=success, reason=reason)


def _resolve_paid_lookup(*, user, ip: str) -> tuple[bool, str]:
    today = timezone.localdate()
    if user and user.is_authenticated:
        if user.last_lookup_on != today:
            return False, "free"
        if user.credits <= 0:
            return True, "no_credits"
        user.consume_credit(save=True)
        CreditLedgerEntry.objects.create(
            recruiter=user,
            entry_type=CreditLedgerEntry.EntryType.SEARCH_CONSUMPTION,
            delta=-1,
            reason="Additional daily lookup",
        )
        return False, "credit"

    used = CandidateViewLog.objects.filter(ip=ip, viewed_at__date=today).exists()
    if used:
        return True, "anon_limit"
    return False, "free"


@transaction.atomic
def create_lookup_session(*, payload: dict, user, ip: str) -> tuple[bool, dict]:
    country = (payload.get("country") or "").strip()
    region = (payload.get("region") or "").strip()
    first_name = (payload.get("first_name") or "").strip()
    gender = (payload.get("gender") or "").strip()

    if not all([country, region, first_name, gender]):
        return False, {"error": "country, region, first_name, and gender are required"}

    blocked, reason = _resolve_paid_lookup(user=user, ip=ip)
    if blocked:
        if reason == "anon_limit":
            return False, {"error": "Anonyme Nutzer koennen nur ein Profil pro Tag aufrufen."}
        return False, {"error": "Keine Credits verfuegbar fuer weitere Suchen heute."}

    candidates = initial_candidate_queryset(country=country, region=region, first_name=first_name, gender=gender)
    candidate_ids = list(candidates.values_list("id", flat=True)[:200])

    session = LookupSession.objects.create(
        requester=user if user and user.is_authenticated else None,
        requester_ip=ip,
        initial_country=country,
        initial_region=region,
        initial_first_name=first_name,
        initial_gender=gender,
        candidate_ids=candidate_ids,
        step_expires_at=timezone.now() + timedelta(seconds=settings.SEARCH_STEP_TIMEOUT_SECONDS),
        requires_credit=(reason == "credit"),
    )

    if user and user.is_authenticated:
        user.mark_lookup(save=True)

    return True, {
        "session_token": session.token.hex,
        "candidate_count": len(candidate_ids),
        "message": "Keine Treffer. Du kannst ein neues Profil anlegen." if not candidate_ids else "Treffer gefunden.",
        "case_options": list(CASE_PIPELINES.keys()),
        "can_create_profile": len(candidate_ids) == 0,
    }


def _get_active_session(token: str, ip: str) -> LookupSession | None:
    try:
        session = LookupSession.objects.get(token=token)
    except LookupSession.DoesNotExist:
        return None
    if session.requester_ip != ip:
        return None
    if session.status != LookupSession.Status.ACTIVE:
        return None
    if session.step_expires_at <= timezone.now():
        session.status = LookupSession.Status.EXPIRED
        session.save(update_fields=["status", "updated_at"])
        return None
    return session


@transaction.atomic
def advance_lookup_session(*, token: str, payload: dict, ip: str) -> tuple[bool, dict]:
    session = _get_active_session(token, ip)
    if session is None:
        register_security_failure(ip=ip, reason="lookup session invalid_or_expired")
        return False, {"error": "Session invalid or expired"}

    step = int(payload.get("step") or session.current_step + 1)
    case_type = (payload.get("case_type") or session.case_type or "").strip().lower()

    if not case_type or case_type not in CASE_PIPELINES:
        return False, {"error": "Valid case_type is required"}

    session.case_type = case_type
    pipeline = CASE_PIPELINES[case_type]
    stage_index = max(0, step - 2)
    if stage_index >= len(pipeline):
        return False, {"error": "Step out of range"}

    expected_field = pipeline[stage_index]
    value = payload.get(expected_field)
    if value in (None, ""):
        return False, {"error": f"{expected_field} is required"}

    base_candidates = Candidate.objects.filter(id__in=session.candidate_ids)
    for idx in range(stage_index):
        prev_field = pipeline[idx]
        prev_value = session.step_payload.get(prev_field)
        if prev_field == "city":
            base_candidates = _city_filter(base_candidates, str(prev_value))
        elif prev_field == "hair_color":
            base_candidates = _hair_color_filter(base_candidates, str(prev_value))
        elif prev_field == "age":
            base_candidates = _age_filter(base_candidates, str(prev_value))
        else:
            base_candidates = _candidate_filter_for_case(case_type, base_candidates, prev_value)

    if expected_field == "city":
        narrowed = _city_filter(base_candidates, str(value))
    elif expected_field == "hair_color":
        narrowed = _hair_color_filter(base_candidates, str(value))
    elif expected_field == "age":
        narrowed = _age_filter(base_candidates, str(value))
    else:
        narrowed = _candidate_filter_for_case(case_type, base_candidates, value)

    narrowed_ids = list(narrowed.values_list("id", flat=True))
    session.step_payload[expected_field] = value
    session.candidate_ids = narrowed_ids
    session.current_step = step

    if not narrowed_ids:
        _record_attempt(session, step=step, ip=ip, success=False, reason=f"No match on {expected_field}")
        session.status = LookupSession.Status.FAILED
        session.save(update_fields=["step_payload", "candidate_ids", "current_step", "status", "updated_at"])
        register_security_failure(ip=ip, reason=f"lookup mismatch {case_type}:{expected_field}")
        return False, {"error": "No candidate matches this step"}

    is_final = stage_index == len(pipeline) - 1 and len(narrowed_ids) == 1
    if is_final:
        candidate = Candidate.objects.get(id=narrowed_ids[0])
        session.status = LookupSession.Status.RESOLVED
        session.matched_candidate = candidate
        session.profile_expires_at = timezone.now() + timedelta(seconds=settings.PROFILE_VIEW_WINDOW_SECONDS)
        session.step_expires_at = timezone.now() + timedelta(seconds=settings.SEARCH_STEP_TIMEOUT_SECONDS)
        session.save(
            update_fields=[
                "step_payload",
                "candidate_ids",
                "current_step",
                "status",
                "matched_candidate",
                "profile_expires_at",
                "step_expires_at",
                "updated_at",
            ]
        )
        _record_attempt(session, step=step, ip=ip, success=True, reason="resolved")
        return True, {"resolved": True, "candidate_id": candidate.id, "profile_token": session.token.hex}

    session.step_expires_at = timezone.now() + timedelta(seconds=settings.SEARCH_STEP_TIMEOUT_SECONDS)
    session.save(
        update_fields=[
            "step_payload",
            "candidate_ids",
            "current_step",
            "step_expires_at",
            "case_type",
            "updated_at",
        ]
    )
    _record_attempt(session, step=step, ip=ip, success=True, reason=f"Matched step {expected_field}")

    return True, {
        "resolved": False,
        "step": step,
        "remaining_candidates": len(narrowed_ids),
        "next_field": pipeline[stage_index + 1],
    }


@transaction.atomic
def reveal_profile(*, token: str, ip: str, user=None) -> tuple[bool, dict]:
    try:
        session = LookupSession.objects.select_related("matched_candidate", "requester").get(token=token)
    except LookupSession.DoesNotExist:
        return False, {"error": "Session not found"}

    if session.requester_ip != ip:
        return False, {"error": "Session IP mismatch"}
    if session.status != LookupSession.Status.RESOLVED or session.matched_candidate is None:
        return False, {"error": "Lookup not resolved"}
    if not session.profile_expires_at or session.profile_expires_at <= timezone.now():
        return False, {"error": "Profile view window expired"}

    candidate = session.matched_candidate
    CandidateViewLog.objects.create(
        candidate=candidate,
        recruiter=user if user and user.is_authenticated else None,
        ip=ip,
    )

    Candidate.objects.filter(id=candidate.id).update(profile_views_count=models.F("profile_views_count") + 1)
    candidate.refresh_from_db()

    payload = {
        "id": candidate.id,
        "first_name": candidate.first_name,
        "masked_last_name": candidate.masked_last_name,
        "age": candidate.current_age,
        "hair_color": candidate.get_hair_color_display(),
        "gender": candidate.get_gender_display(),
        "masked_email": candidate.masked_email,
        "masked_phone": candidate.masked_phone,
        "country": candidate.country,
        "region": candidate.region,
        "city": candidate.city,
        "profile_views_count": candidate.profile_views_count,
        "distinct_recruiter_count": candidate.distinct_recruiter_count,
    }
    return True, payload


@transaction.atomic
def cast_votes(*, candidate_id: int, recruiter, attribute_codes: list[int], anonymous: bool) -> tuple[bool, dict]:
    if not recruiter.is_authenticated:
        return False, {"error": "Authentication required"}
    if not recruiter.is_verified_recruiter:
        return False, {"error": "Recruiter verification required"}
    if not recruiter.can_vote_today():
        return False, {"error": "Voting cooldown active"}
    if len(attribute_codes) == 0 or len(attribute_codes) > 3:
        return False, {"error": "Select between 1 and 3 attributes"}

    candidate = Candidate.objects.filter(id=candidate_id).first()
    if candidate is None:
        return False, {"error": "Candidate not found"}

    if CandidateAttributeVote.objects.filter(candidate=candidate, recruiter=recruiter).exists():
        return False, {"error": "Recruiter already voted this candidate"}

    attrs = list(CandidateAttributeDefinition.objects.filter(code__in=attribute_codes, is_active=True))
    if len(attrs) != len(set(attribute_codes)):
        return False, {"error": "Invalid attribute selection"}

    prior_recruiters = list(
        CandidateAttributeVote.objects.filter(candidate=candidate, recruiter__isnull=False)
        .exclude(recruiter=recruiter)
        .values_list("recruiter__email", "recruiter__notify_on_vote_overlap")
        .distinct()
    )

    for attr in attrs:
        CandidateAttributeVote.objects.create(
            candidate=candidate,
            attribute=attr,
            recruiter=recruiter,
            is_anonymous=anonymous,
            voted_on=timezone.localdate(),
        )

    recruiter.mark_vote(save=True)
    recruiter.add_credits(1, save=True)
    CreditLedgerEntry.objects.create(
        recruiter=recruiter,
        entry_type=CreditLedgerEntry.EntryType.EXISTING_VOTE_REWARD,
        delta=1,
        reason=f"Voted candidate #{candidate.id}",
    )
    candidate.distinct_recruiter_count = (
        CandidateAttributeVote.objects.filter(candidate=candidate, recruiter__isnull=False)
        .values("recruiter")
        .distinct()
        .count()
    )
    candidate.save(update_fields=["distinct_recruiter_count", "updated_at"])

    for email, notify_enabled in prior_recruiters:
        if not email or not notify_enabled:
            continue
        candidate_display = f"{candidate.first_name} {candidate.masked_last_name}"
        send_mail(
            subject=f"{settings.PROJECT_NAME}: Neue Bewertung zu gemeinsamem Profil",
            message=(
                f"Ein weiterer Recruiter hat das Profil von {candidate_display} bewertet.\n"
                "Wenn du Kontakt aufnehmen willst, nutze den sicheren Relay-Flow im Dashboard."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )

    return True, {"ok": True, "candidate_id": candidate.id, "vote_count": len(attrs), "credits_awarded": 1}


@transaction.atomic
def create_candidate_record(*, payload: dict, recruiter) -> tuple[bool, dict]:
    if not recruiter or not recruiter.is_authenticated:
        return False, {"error": "Authentication required"}
    if not recruiter.can_create_profile_this_week():
        return False, {"error": "Weekly candidate creation limit reached"}

    required = ["first_name", "last_name", "gender", "country", "region", "city"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return False, {"error": f"Missing required fields: {', '.join(missing)}"}

    candidate = Candidate.objects.create(
        first_name=str(payload["first_name"]).strip(),
        last_name=str(payload["last_name"]).strip(),
        gender=str(payload["gender"]).strip(),
        birth_date=payload.get("birth_date") or None,
        age_years=payload.get("age") or None,
        country=str(payload["country"]).strip(),
        region=str(payload["region"]).strip(),
        city=str(payload["city"]).strip(),
        hair_color=int(payload.get("hair_color") or HairColor.OTHER),
        primary_email=str(payload.get("email") or "").strip().lower(),
        primary_phone=str(payload.get("phone") or "").strip(),
        dating_profile_url=str(payload.get("social_url") or "").strip(),
        created_by=recruiter,
    )

    recruiter.mark_profile_created(save=True)
    recruiter.add_credits(2, save=True)
    CreditLedgerEntry.objects.create(
        recruiter=recruiter,
        entry_type=CreditLedgerEntry.EntryType.NEW_CANDIDATE_REWARD,
        delta=2,
        reason=f"Created candidate #{candidate.id}",
    )

    return True, {"candidate_id": candidate.id, "credits_awarded": 2}


@transaction.atomic
def submit_candidate_enrichment(*, candidate_id: int, payload: dict, recruiter) -> tuple[bool, dict]:
    if not recruiter or not recruiter.is_authenticated:
        return False, {"error": "Authentication required"}
    candidate = Candidate.objects.filter(id=candidate_id).first()
    if candidate is None:
        return False, {"error": "Candidate not found"}

    editable_fields = {
        "secondary_email",
        "secondary_phone",
        "hair_color",
        "country",
        "region",
        "city",
        "dating_profile_url",
    }
    proposed = {key: value for key, value in payload.items() if key in editable_fields and str(value).strip()}
    if len(proposed) < 1:
        return False, {"error": "No editable fields provided"}

    submission = DataEnrichmentSubmission.objects.create(
        candidate=candidate,
        recruiter=recruiter,
        payload=proposed,
    )

    if len(proposed) >= 2:
        recruiter.add_credits(1, save=True)
        CreditLedgerEntry.objects.create(
            recruiter=recruiter,
            entry_type=CreditLedgerEntry.EntryType.ENRICHMENT_REWARD,
            delta=1,
            reason=f"Enrichment submission #{submission.id}",
        )

    return True, {"submission_id": submission.id, "status": submission.status}

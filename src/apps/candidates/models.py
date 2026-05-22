from __future__ import annotations

import re
import uuid
from datetime import date
from urllib.parse import urlparse

from django.conf import settings
from django.db import models
from django.utils import timezone
from rapidfuzz import fuzz
from unidecode import unidecode


def normalize_token(value: str) -> str:
    text = unidecode((value or "").strip().lower())
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class CandidateGender(models.TextChoices):
    FEMALE = "female", "Weiblich"
    MALE = "male", "Maennlich"
    DIVERSE = "diverse", "Divers"


class HairColor(models.IntegerChoices):
    BLACK = 1, "Schwarz"
    BROWN = 2, "Braun"
    BLONDE = 3, "Blond"
    RED = 4, "Rot"
    GRAY = 5, "Grau"
    OTHER = 6, "Andere"


class SocialPlatform(models.IntegerChoices):
    TINDER = 1, "Tinder"
    BUMBLE = 2, "Bumble"
    HINGE = 3, "Hinge"
    OKCUPID = 4, "OkCupid"
    MATCH = 5, "Match"
    POF = 6, "PlentyOfFish"
    BADOO = 7, "Badoo"
    HAPPN = 8, "Happn"


SOCIAL_DOMAIN_MAP: dict[int, tuple[str, ...]] = {
    SocialPlatform.TINDER: ("tinder.com",),
    SocialPlatform.BUMBLE: ("bumble.com",),
    SocialPlatform.HINGE: ("hinge.co", "hinge.com"),
    SocialPlatform.OKCUPID: ("okcupid.com",),
    SocialPlatform.MATCH: ("match.com",),
    SocialPlatform.POF: ("pof.com", "plentyoffish.com"),
    SocialPlatform.BADOO: ("badoo.com",),
    SocialPlatform.HAPPN: ("happn.com",),
}


def detect_social_platform(url: str) -> int | None:
    try:
        parsed = urlparse((url or "").strip())
    except ValueError:
        return None
    host = (parsed.netloc or "").lower().strip()
    if host.startswith("www."):
        host = host[4:]
    if parsed.scheme not in {"http", "https"}:
        return None
    for platform, domains in SOCIAL_DOMAIN_MAP.items():
        if any(host == domain or host.endswith(f".{domain}") for domain in domains):
            return int(platform)
    return None


class Candidate(models.Model):
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    first_name_norm = models.CharField(max_length=120, db_index=True)
    last_name_norm = models.CharField(max_length=120, db_index=True)

    gender = models.CharField(max_length=16, choices=CandidateGender.choices)
    birth_date = models.DateField(null=True, blank=True)
    age_years = models.PositiveSmallIntegerField(null=True, blank=True)

    country = models.CharField(max_length=120)
    region = models.CharField(max_length=120)
    city = models.CharField(max_length=120)

    hair_color = models.PositiveSmallIntegerField(choices=HairColor.choices, default=HairColor.OTHER)

    primary_email = models.EmailField(blank=True)
    secondary_email = models.EmailField(blank=True)
    primary_phone = models.CharField(max_length=32, blank=True)
    secondary_phone = models.CharField(max_length=32, blank=True)

    dating_profile_url = models.URLField(blank=True)
    dating_platform = models.PositiveSmallIntegerField(choices=SocialPlatform.choices, null=True, blank=True)

    profile_views_count = models.PositiveIntegerField(default=0)
    distinct_recruiter_count = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_candidates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate"
        indexes = [
            models.Index(fields=["country", "region", "city"]),
            models.Index(fields=["gender", "country", "region"]),
            models.Index(fields=["first_name_norm", "last_name_norm"]),
        ]

    def save(self, *args, **kwargs):
        self.first_name_norm = normalize_token(self.first_name)
        self.last_name_norm = normalize_token(self.last_name)
        if self.dating_profile_url:
            self.dating_platform = detect_social_platform(self.dating_profile_url)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def current_age(self) -> int | None:
        if self.birth_date:
            today = timezone.localdate()
            years = today.year - self.birth_date.year
            if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
                years -= 1
            return max(0, years)
        return self.age_years

    @property
    def masked_last_name(self) -> str:
        return self._mask_text(self.last_name)

    @property
    def masked_email(self) -> str:
        return self._mask_email(self.primary_email)

    @property
    def masked_phone(self) -> str:
        return self._mask_phone(self.primary_phone)

    def _mask_text(self, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 2:
            return value[0] + "*"
        return value[0] + "*" * (len(value) - 2) + value[-1]

    def _mask_email(self, email: str) -> str:
        if not email or "@" not in email:
            return ""
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            local_mask = local[0] + "*"
        else:
            local_mask = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{local_mask}@{domain}"

    def _mask_phone(self, phone: str) -> str:
        cleaned = re.sub(r"\s+", "", phone or "")
        if len(cleaned) <= 4:
            return "*" * len(cleaned)
        return cleaned[:2] + "*" * (len(cleaned) - 4) + cleaned[-2:]

    def fuzzy_match_first_name(self, value: str) -> bool:
        needle = normalize_token(value)
        if not needle:
            return False
        if needle == self.first_name_norm:
            return True
        return fuzz.ratio(needle, self.first_name_norm) >= 84

    def fuzzy_match_last_name(self, value: str) -> bool:
        needle = normalize_token(value)
        if not needle:
            return False
        if needle == self.last_name_norm:
            return True
        return fuzz.ratio(needle, self.last_name_norm) >= 84

    def public_vote_breakdown(self) -> list[dict[str, object]]:
        today = timezone.localdate()
        rows = (
            CandidateAttributeVote.objects.filter(candidate=self, is_visible=True)
            .filter(models.Q(expires_on__isnull=True) | models.Q(expires_on__gt=today))
            .values("attribute__label", "attribute__icon")
            .annotate(count=models.Count("id"))
            .order_by("-count", "attribute__label")
        )
        return [
            {
                "label": row["attribute__label"],
                "icon": row["attribute__icon"],
                "count": row["count"],
            }
            for row in rows
        ]


class CandidateAttributeDefinition(models.Model):
    code = models.PositiveSmallIntegerField(unique=True)
    slug = models.SlugField(max_length=64, unique=True)
    label = models.CharField(max_length=120)
    icon = models.CharField(max_length=8, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "candidate_attribute_definition"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code}:{self.label}"


class CandidateAttributeVote(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="votes")
    attribute = models.ForeignKey(CandidateAttributeDefinition, on_delete=models.CASCADE, related_name="votes")
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidate_votes",
    )
    is_anonymous = models.BooleanField(default=False)
    voted_on = models.DateField(default=timezone.localdate)
    expires_on = models.DateField(null=True, blank=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        db_table = "candidate_attribute_vote"
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "recruiter", "attribute"],
                name="uniq_candidate_recruiter_attribute",
            ),
        ]
        indexes = [models.Index(fields=["candidate", "voted_on"])]

    def save(self, *args, **kwargs):
        if self.expires_on is None and self.voted_on:
            years = max(1, int(getattr(settings, "VOTE_RETENTION_YEARS", 5)))
            try:
                self.expires_on = date(self.voted_on.year + years, self.voted_on.month, self.voted_on.day)
            except ValueError:
                self.expires_on = date(self.voted_on.year + years, self.voted_on.month, 28)
        super().save(*args, **kwargs)


class CandidateViewLog(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="view_logs")
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="candidate_view_logs",
    )
    ip = models.GenericIPAddressField()
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "candidate_view_log"
        indexes = [models.Index(fields=["candidate", "viewed_at"]), models.Index(fields=["ip", "viewed_at"])]


class LookupSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESOLVED = "resolved", "Resolved"
        EXPIRED = "expired", "Expired"
        FAILED = "failed", "Failed"

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lookup_sessions",
    )
    requester_ip = models.GenericIPAddressField()
    initial_country = models.CharField(max_length=120)
    initial_region = models.CharField(max_length=120)
    initial_first_name = models.CharField(max_length=120)
    initial_gender = models.CharField(max_length=16)
    candidate_ids = models.JSONField(default=list)

    case_type = models.CharField(max_length=32, blank=True)
    current_step = models.PositiveSmallIntegerField(default=1)
    step_payload = models.JSONField(default=dict)

    matched_candidate = models.ForeignKey(
        Candidate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lookup_matches",
    )

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    requires_credit = models.BooleanField(default=False)
    step_expires_at = models.DateTimeField()
    profile_expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lookup_session"
        indexes = [models.Index(fields=["token"]), models.Index(fields=["status", "updated_at"])]


class LookupAttempt(models.Model):
    session = models.ForeignKey(LookupSession, on_delete=models.CASCADE, related_name="attempts")
    step = models.PositiveSmallIntegerField()
    ip = models.GenericIPAddressField()
    success = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lookup_attempt"
        indexes = [models.Index(fields=["ip", "created_at"])]

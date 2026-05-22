from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .managers import RecruiterUserManager


class RecruiterUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=120, blank=True)
    credits = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_verified_recruiter = models.BooleanField(default=False)

    notify_on_vote_overlap = models.BooleanField(default=True)
    notify_on_contact_requests = models.BooleanField(default=True)
    notify_on_security = models.BooleanField(default=True)

    last_lookup_on = models.DateField(null=True, blank=True)
    last_vote_on = models.DateField(null=True, blank=True)
    weekly_profile_creates = models.PositiveSmallIntegerField(default=0)
    weekly_profile_creates_anchor = models.DateField(null=True, blank=True)

    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = RecruiterUserManager()

    class Meta:
        db_table = "recruiter_user"

    def __str__(self) -> str:
        return self.email

    def add_credits(self, amount: int, *, save: bool = True) -> None:
        if amount <= 0:
            return
        self.credits += amount
        if save:
            self.save(update_fields=["credits"])

    def consume_credit(self, *, save: bool = True) -> bool:
        if self.credits <= 0:
            return False
        self.credits -= 1
        if save:
            self.save(update_fields=["credits"])
        return True

    def can_vote_today(self) -> bool:
        if self.last_vote_on is None:
            return True
        days = max(1, int(getattr(settings, "VOTE_COOLDOWN_DAYS", 3)))
        return self.last_vote_on <= timezone.localdate() - timedelta(days=days)

    def mark_vote(self, *, save: bool = True) -> None:
        self.last_vote_on = timezone.localdate()
        if save:
            self.save(update_fields=["last_vote_on"])

    def can_lookup_today(self) -> bool:
        return self.last_lookup_on != timezone.localdate()

    def mark_lookup(self, *, save: bool = True) -> None:
        self.last_lookup_on = timezone.localdate()
        if save:
            self.save(update_fields=["last_lookup_on"])

    def can_create_profile_this_week(self) -> bool:
        today = timezone.localdate()
        if self.weekly_profile_creates_anchor is None:
            return True
        if (today - self.weekly_profile_creates_anchor).days >= 7:
            return True
        return self.weekly_profile_creates < max(1, int(getattr(settings, "AUTH_NEW_RECORDS_PER_WEEK", 1)))

    def mark_profile_created(self, *, save: bool = True) -> None:
        today = timezone.localdate()
        if self.weekly_profile_creates_anchor is None or (today - self.weekly_profile_creates_anchor).days >= 7:
            self.weekly_profile_creates_anchor = today
            self.weekly_profile_creates = 1
        else:
            self.weekly_profile_creates += 1
        if save:
            self.save(update_fields=["weekly_profile_creates", "weekly_profile_creates_anchor"])


class RecruiterSecurityVerification(models.Model):
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_verifications",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recruiter_security_verification"
        indexes = [models.Index(fields=["token"]), models.Index(fields=["recruiter", "is_completed"])]

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def mark_completed(self) -> None:
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=["is_completed", "completed_at"])


class RecruiterContactRelay(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="initiated_contact_relays",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_contact_relays",
    )
    candidate_id = models.PositiveBigIntegerField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "recruiter_contact_relay"
        indexes = [models.Index(fields=["candidate_id", "status"])]

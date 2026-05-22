from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class CreditLedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        PURCHASE = "purchase", "Purchase"
        SEARCH_CONSUMPTION = "search_consumption", "Search Consumption"
        NEW_CANDIDATE_REWARD = "new_candidate_reward", "New Candidate Reward"
        EXISTING_VOTE_REWARD = "existing_vote_reward", "Existing Vote Reward"
        ENRICHMENT_REWARD = "enrichment_reward", "Enrichment Reward"
        MANUAL_ADJUSTMENT = "manual_adjustment", "Manual Adjustment"

    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="credit_ledger")
    entry_type = models.CharField(max_length=32, choices=EntryType.choices)
    delta = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "credit_ledger_entry"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recruiter", "created_at"])]


class CreditPurchase(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="credit_purchases")
    credits_purchased = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    stripe_session_id = models.CharField(max_length=255, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "credit_purchase"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recruiter", "status"])]

    def complete(self) -> None:
        if self.status == self.Status.COMPLETED:
            return
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

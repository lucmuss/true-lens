from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.candidates.models import Candidate


class DataEnrichmentSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="enrichment_submissions",
    )
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrichment_submissions",
    )
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    moderator_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "data_enrichment_submission"
        indexes = [models.Index(fields=["status", "created_at"])]


class SupporterNodeApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    applicant_name = models.CharField(max_length=120)
    applicant_email = models.EmailField()
    base_url = models.URLField()
    public_key = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    moderator_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "supporter_node_application"

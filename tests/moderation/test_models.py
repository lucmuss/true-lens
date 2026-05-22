from __future__ import annotations

import pytest

from apps.moderation.models import DataEnrichmentSubmission, SupporterNodeApplication


@pytest.mark.django_db
def test_enrichment_submission_defaults_pending(candidate_factory, recruiter_factory):
    item = DataEnrichmentSubmission.objects.create(
        candidate=candidate_factory(),
        recruiter=recruiter_factory(),
        payload={"city": "Hamburg"},
    )
    assert item.status == DataEnrichmentSubmission.Status.PENDING


@pytest.mark.django_db
def test_supporter_application_defaults_pending():
    app = SupporterNodeApplication.objects.create(
        applicant_name="Supporter",
        applicant_email="supporter@example.com",
        base_url="https://node.example.com",
    )
    assert app.status == SupporterNodeApplication.Status.PENDING

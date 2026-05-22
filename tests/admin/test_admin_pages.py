from __future__ import annotations

import pytest
from django.contrib import admin
from django.test import Client
from django.urls import reverse

from apps.accounts.models import RecruiterUser
from apps.candidates.models import (
    Candidate,
    CandidateAttributeDefinition,
    CandidateAttributeVote,
    CandidateViewLog,
    LookupAttempt,
    LookupSession,
)
from apps.credits.models import CreditLedgerEntry, CreditPurchase
from apps.moderation.models import DataEnrichmentSubmission, SupporterNodeApplication
from apps.replication.models import NodeInstance, ReplicationEvent, ReplicationJob
from apps.security.models import ApiGateToken, CaptchaChallenge, IPBan, SecurityEvent


@pytest.mark.django_db
def test_admin_index_redirects_for_anonymous_user(client):
    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert reverse("admin:login") in response.url


@pytest.mark.django_db
def test_admin_index_loads_for_superuser(superuser):
    client = Client()
    client.force_login(superuser)

    response = client.get(reverse("admin:index"))

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    [
        "admin:accounts_recruiteruser_changelist",
        "admin:accounts_recruitersecurityverification_changelist",
        "admin:accounts_recruitercontactrelay_changelist",
        "admin:candidates_candidate_changelist",
        "admin:candidates_candidateattributedefinition_changelist",
        "admin:candidates_candidateattributevote_changelist",
        "admin:candidates_candidateviewlog_changelist",
        "admin:candidates_lookupsession_changelist",
        "admin:candidates_lookupattempt_changelist",
        "admin:credits_creditledgerentry_changelist",
        "admin:credits_creditpurchase_changelist",
        "admin:moderation_dataenrichmentsubmission_changelist",
        "admin:moderation_supporternodeapplication_changelist",
        "admin:replication_nodeinstance_changelist",
        "admin:replication_replicationjob_changelist",
        "admin:replication_replicationevent_changelist",
        "admin:security_captchachallenge_changelist",
        "admin:security_apigatetoken_changelist",
        "admin:security_ipban_changelist",
        "admin:security_securityevent_changelist",
    ],
)
def test_admin_changelist_pages_load_for_superuser(superuser, url_name):
    client = Client()
    client.force_login(superuser)

    response = client.get(reverse(url_name))

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_registers_all_project_models():
    for model in [
        RecruiterUser,
        Candidate,
        CandidateAttributeDefinition,
        CandidateAttributeVote,
        CandidateViewLog,
        LookupSession,
        LookupAttempt,
        CreditLedgerEntry,
        CreditPurchase,
        DataEnrichmentSubmission,
        SupporterNodeApplication,
        NodeInstance,
        ReplicationJob,
        ReplicationEvent,
        CaptchaChallenge,
        ApiGateToken,
        IPBan,
        SecurityEvent,
    ]:
        assert model in admin.site._registry


@pytest.mark.django_db
def test_recruiter_user_admin_exposes_credit_and_verification_fields():
    admin_obj = admin.site._registry[RecruiterUser]

    assert "credits" in admin_obj.list_display
    assert "is_verified_recruiter" in admin_obj.list_display
    assert "notify_on_vote_overlap" in admin_obj.fieldsets[1][1]["fields"]

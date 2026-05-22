from __future__ import annotations

import pytest
from django.urls import resolve, reverse


@pytest.mark.parametrize(
    "name,kwargs",
    [
        ("landing", {}),
        ("dashboard", {}),
        ("vote_history", {}),
        ("admin_dashboard", {}),
        ("candidate_profile", {"candidate_id": 1}),
        ("account_security_verify", {"token": "abc"}),
        ("recruiter_settings", {}),
        ("recruiter_delete", {}),
        ("api_captcha_start", {}),
        ("api_captcha_verify", {}),
        ("api_contact_request_create", {}),
        ("api_contact_request_accept", {"relay_id": 1}),
        ("api_contact_request_reject", {"relay_id": 1}),
        ("api_country_autocomplete", {}),
        ("api_region_autocomplete", {}),
        ("api_city_autocomplete", {}),
        ("api_search_start", {}),
        ("api_search_step", {"step": 2}),
        ("api_search_status", {"token": "abc"}),
        ("api_search_profile", {"token": "abc"}),
        ("api_candidate_create", {}),
        ("api_candidate_enrichment", {"candidate_id": 1}),
        ("api_candidate_vote", {"candidate_id": 1}),
        ("api_candidate_votes", {"candidate_id": 1}),
        ("api_credit_checkout", {}),
        ("api_stripe_webhook", {}),
        ("api_wallet", {}),
        ("api_moderation_queue", {}),
        ("api_moderation_queue_approve", {"item_id": 1}),
        ("api_moderation_queue_reject", {"item_id": 1}),
        ("api_internal_heartbeat", {}),
        ("api_internal_election", {}),
        ("api_internal_repl_push", {}),
        ("api_internal_repl_ack", {}),
    ],
)
def test_reverse_and_resolve(name, kwargs):
    path = reverse(name, kwargs=kwargs)
    match = resolve(path)
    assert match.url_name == name


@pytest.mark.django_db
def test_healthz_endpoint(client):
    response = client.get("/healthz/")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert response.content.decode() == "ok"


@pytest.mark.django_db
def test_unknown_url_returns_404(client):
    response = client.get("/no-such-route/")
    assert response.status_code == 404

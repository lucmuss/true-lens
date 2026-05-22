from __future__ import annotations

import json
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.candidates.models import CandidateGender, LookupSession


@pytest.mark.django_db
def test_country_autocomplete_returns_suggestions(client, js_gate_headers):
    response = client.get("/api/search/countries", **js_gate_headers)
    assert response.status_code == 200
    assert "suggestions" in response.json()


@pytest.mark.django_db
def test_region_autocomplete_filters_by_country(client, js_gate_headers):
    response = client.get("/api/search/regions", {"country": "Germany", "q": "ber"}, **js_gate_headers)
    assert response.status_code == 200
    labels = [s["label"].lower() for s in response.json()["suggestions"]]
    assert any("ber" in label for label in labels) or labels == []


@pytest.mark.django_db
def test_city_autocomplete_short_query_returns_empty(client, js_gate_headers):
    response = client.get("/api/search/cities", {"q": "a"}, **js_gate_headers)
    assert response.status_code == 200
    assert response.json()["suggestions"] == []


@pytest.mark.django_db
def test_city_autocomplete_google_error_returns_503(client, js_gate_headers, monkeypatch):
    def _boom(*args, **kwargs):
        from apps.candidates.google_places import GooglePlacesError

        raise GooglePlacesError("down")

    monkeypatch.setattr("apps.candidates.api_views.autocomplete_cities", _boom)

    response = client.get("/api/search/cities", {"q": "berlin", "country": "Germany"}, **js_gate_headers)
    assert response.status_code == 503


@pytest.mark.django_db
def test_search_start_requires_fields(client, js_gate_headers):
    response = client.post(
        "/api/search/start",
        data=json.dumps({"country": "Germany"}),
        content_type="application/json",
        **js_gate_headers,
    )
    assert response.status_code == 400
    assert response.json()["ok"] is False


@pytest.mark.django_db
def test_search_start_returns_case_options(client, candidate_factory, js_gate_headers):
    candidate_factory(first_name="Clara", gender=CandidateGender.FEMALE, country="Germany", region="Berlin")

    response = client.post(
        "/api/search/start",
        data=json.dumps(
            {
                "country": "Germany",
                "region": "Berlin",
                "first_name": "Clara",
                "gender": CandidateGender.FEMALE,
            }
        ),
        content_type="application/json",
        **js_gate_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert "session_token" in payload
    assert "case_options" in payload


@pytest.mark.django_db
def test_search_step_invalid_case_type(client, lookup_session_factory, js_gate_headers):
    session = lookup_session_factory()

    response = client.post(
        "/api/search/step/2",
        data=json.dumps({"session_token": session.token.hex, "case_type": "bad"}),
        content_type="application/json",
        **js_gate_headers,
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_search_status_404_for_wrong_ip(client, lookup_session_factory, make_js_gate_headers):
    session = lookup_session_factory(requester_ip="10.0.0.1")
    headers = make_js_gate_headers(ip="127.0.0.1")

    response = client.get(f"/api/search/session/{session.token.hex}/status", **headers)
    assert response.status_code == 404


@pytest.mark.django_db
def test_search_profile_rejects_unresolved_session(client, lookup_session_factory, js_gate_headers):
    session = lookup_session_factory(status=LookupSession.Status.ACTIVE)

    response = client.get(f"/api/search/session/{session.token.hex}/profile", **js_gate_headers)
    assert response.status_code == 400


@pytest.mark.django_db
def test_search_profile_rejects_expired_profile_window(client, candidate_factory, lookup_session_factory, js_gate_headers):
    candidate = candidate_factory()
    session = lookup_session_factory(
        matched_candidate=candidate,
        status=LookupSession.Status.RESOLVED,
        profile_expires_at=timezone.now() - timedelta(seconds=1),
    )

    response = client.get(f"/api/search/session/{session.token.hex}/profile", **js_gate_headers)

    assert response.status_code == 400
    assert response.json()["ok"] is False


@pytest.mark.django_db
def test_search_start_get_method_not_allowed(client, js_gate_headers):
    response = client.get("/api/search/start", **js_gate_headers)
    assert response.status_code == 405

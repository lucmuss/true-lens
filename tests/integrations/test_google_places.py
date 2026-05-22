from __future__ import annotations

import pytest
from django.test import override_settings

from apps.candidates.google_places import (
    GOOGLE_PLACES_AUTOCOMPLETE_URL,
    GooglePlacesError,
    autocomplete_cities,
)


class _DummyResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _RecordingSession:
    def __init__(self, response: _DummyResponse):
        self.response = response
        self.calls: list[dict] = []

    def post(self, url, *, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers or {}, "json": json or {}, "timeout": timeout})
        return self.response


@override_settings(GOOGLE_PLACES_API_KEY="test-key")
def test_autocomplete_cities_short_query_skips_http_call():
    session = _RecordingSession(_DummyResponse(200, {"suggestions": []}))

    assert autocomplete_cities("a", requests_session=session) == []
    assert session.calls == []


@override_settings(GOOGLE_PLACES_API_KEY="")
def test_autocomplete_cities_without_api_key_skips_http_call():
    session = _RecordingSession(_DummyResponse(200, {"suggestions": []}))

    assert autocomplete_cities("berlin", requests_session=session) == []
    assert session.calls == []


@override_settings(GOOGLE_PLACES_API_KEY="test-key")
def test_autocomplete_cities_success_builds_expected_payload_and_parses_result():
    session = _RecordingSession(
        _DummyResponse(
            200,
            {
                "suggestions": [
                    {
                        "placePrediction": {
                            "placeId": "abc123",
                            "text": {"text": "Berlin, Germany"},
                        }
                    },
                    {
                        "placePrediction": {
                            "placeId": "def456",
                            "text": {"text": "Bern, Switzerland"},
                        }
                    },
                ]
            },
        )
    )

    result = autocomplete_cities(
        "ber",
        country_code="DE",
        region="Berlin",
        session_token="session-1",
        requests_session=session,
    )

    assert [item.text for item in result] == ["Berlin, Germany", "Bern, Switzerland"]
    assert [item.place_id for item in result] == ["abc123", "def456"]

    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["url"] == GOOGLE_PLACES_AUTOCOMPLETE_URL
    assert call["headers"]["X-Goog-Api-Key"] == "test-key"
    assert call["json"] == {
        "input": "ber, Berlin",
        "includedPrimaryTypes": ["(cities)"],
        "includedRegionCodes": ["de"],
        "sessionToken": "session-1",
    }


@override_settings(GOOGLE_PLACES_API_KEY="test-key")
def test_autocomplete_cities_filters_empty_text_items():
    session = _RecordingSession(
        _DummyResponse(
            200,
            {
                "suggestions": [
                    {"placePrediction": {"placeId": "a1", "text": {"text": ""}}},
                    {"placePrediction": {"placeId": "a2", "text": {"text": "Hamburg, Germany"}}},
                    {"placePrediction": {}},
                ]
            },
        )
    )

    result = autocomplete_cities("ha", requests_session=session)

    assert [(item.text, item.place_id) for item in result] == [("Hamburg, Germany", "a2")]


@override_settings(GOOGLE_PLACES_API_KEY="test-key")
def test_autocomplete_cities_raises_google_places_error_on_http_failure():
    session = _RecordingSession(_DummyResponse(503, {"error": "unavailable"}))

    with pytest.raises(GooglePlacesError, match="503"):
        autocomplete_cities("berlin", requests_session=session)

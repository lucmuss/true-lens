from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings

GOOGLE_PLACES_AUTOCOMPLETE_URL = "https://places.googleapis.com/v1/places:autocomplete"


class GooglePlacesError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlaceSuggestion:
    text: str
    place_id: str


def autocomplete_cities(
    query: str,
    *,
    country_code: str = "",
    region: str = "",
    session_token: str = "",
    requests_session=None,
) -> list[PlaceSuggestion]:
    q = (query or "").strip()
    if len(q) < 2:
        return []

    api_key = (settings.GOOGLE_PLACES_API_KEY or "").strip()
    if not api_key:
        return []

    payload: dict[str, object] = {
        "input": ", ".join(part for part in [q, region] if part),
        "includedPrimaryTypes": ["(cities)"],
    }
    if country_code:
        payload["includedRegionCodes"] = [country_code.lower()]
    if session_token:
        payload["sessionToken"] = session_token

    session = requests_session or requests
    response = session.post(
        GOOGLE_PLACES_AUTOCOMPLETE_URL,
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "suggestions.placePrediction.placeId,suggestions.placePrediction.text.text",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=10,
    )
    if response.status_code >= 400:
        raise GooglePlacesError(f"Google Places request failed: {response.status_code}")

    suggestions: list[PlaceSuggestion] = []
    for item in response.json().get("suggestions", []):
        pred = item.get("placePrediction") or {}
        text = ((pred.get("text") or {}).get("text") or "").strip()
        place_id = (pred.get("placeId") or "").strip()
        if text:
            suggestions.append(PlaceSuggestion(text=text, place_id=place_id))
    return suggestions

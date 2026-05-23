"""Tests that captcha endpoints work without CSRF token (csrf_exempt)."""
import json

import pytest
from django.test import Client


@pytest.mark.django_db
def test_captcha_start_no_csrf():
    """captcha_start must succeed without X-CSRFToken header."""
    client = Client(enforce_csrf_checks=True)
    response = client.post(
        "/api/security/captcha/start",
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "captcha_id" in data
    assert "image_url" in data
    assert "question" in data


@pytest.mark.django_db
def test_captcha_verify_wrong_code_no_csrf():
    """captcha_verify must be reachable without CSRF token (even if code is wrong)."""
    client = Client(enforce_csrf_checks=True)
    start = client.post("/api/security/captcha/start", content_type="application/json")
    captcha_id = start.json()["captcha_id"]

    response = client.post(
        "/api/security/captcha/verify",
        data=json.dumps({"captcha_id": captcha_id, "code": "WRONG"}),
        content_type="application/json",
    )
    # Should be 400 (wrong code), not 403 (CSRF failure)
    assert response.status_code == 400
    assert response.json()["ok"] is False

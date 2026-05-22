from __future__ import annotations

import json

import pytest

from apps.security.models import ApiGateToken, CaptchaChallenge


@pytest.mark.django_db
def test_captcha_start_returns_challenge(client):
    response = client.post("/api/security/captcha/start")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "captcha_id" in data
    assert "image_b64" not in data

    # Verify the image endpoint serves the PNG
    img_response = client.get(f"/api/security/captcha/image/{data['captcha_id']}")
    assert img_response.status_code == 200
    assert img_response["Content-Type"] == "image/png"


@pytest.mark.django_db
def test_captcha_start_rejects_get(client):
    response = client.get("/api/security/captcha/start")
    assert response.status_code == 405


@pytest.mark.django_db
def test_captcha_verify_requires_fields(client):
    response = client.post(
        "/api/security/captcha/verify",
        data=json.dumps({"captcha_id": ""}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["ok"] is False


@pytest.mark.django_db
def test_captcha_verify_rejects_invalid_code(client, captcha_challenge_factory):
    challenge = captcha_challenge_factory(code="ABCD12")

    response = client.post(
        "/api/security/captcha/verify",
        data=json.dumps({"captcha_id": challenge.captcha_id.hex, "code": "WRONG1"}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["ok"] is False


@pytest.mark.django_db
def test_captcha_verify_success_returns_js_gate_token(client, captcha_challenge_factory):
    challenge = captcha_challenge_factory(code="ABCD12")

    response = client.post(
        "/api/security/captcha/verify",
        data=json.dumps({"captcha_id": challenge.captcha_id.hex, "code": "ABCD12"}),
        content_type="application/json",
        HTTP_USER_AGENT="pytest-agent",
        REMOTE_ADDR="127.0.0.1",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["js_gate_token"]

    assert ApiGateToken.objects.filter(token=payload["js_gate_token"]).exists()
    assert CaptchaChallenge.objects.get(id=challenge.id).solved_at is not None


@pytest.mark.django_db
def test_captcha_verify_rejects_get(client):
    response = client.get("/api/security/captcha/verify")
    assert response.status_code == 405

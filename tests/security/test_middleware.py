from __future__ import annotations

import json

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from apps.security.middleware import ApiGateMiddleware, RequestFingerprintMiddleware


@pytest.mark.django_db
def test_request_fingerprint_uses_x_forwarded_for_first_ip():
    rf = RequestFactory()
    request = rf.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8", HTTP_USER_AGENT="pytest")

    middleware = RequestFingerprintMiddleware(lambda req: HttpResponse("ok"))
    response = middleware(request)

    assert response.status_code == 200
    assert request.client_ip == "1.2.3.4"
    assert request.client_ua == "pytest"


@pytest.mark.django_db
def test_apigate_allows_captcha_path_without_js_token(monkeypatch):
    rf = RequestFactory()
    request = rf.post("/api/security/captcha/start")
    request.client_ip = "127.0.0.1"
    request.client_ua = "ua"

    monkeypatch.setattr("apps.security.middleware.is_ip_banned", lambda _ip: False)

    middleware = ApiGateMiddleware(lambda req: HttpResponse("ok"))
    response = middleware(request)

    assert response.status_code == 200


@pytest.mark.django_db
def test_apigate_blocks_when_ip_is_banned(monkeypatch):
    rf = RequestFactory()
    request = rf.get("/api/search/countries")
    request.client_ip = "127.0.0.1"
    request.client_ua = "ua"

    monkeypatch.setattr("apps.security.middleware.is_ip_banned", lambda _ip: True)

    middleware = ApiGateMiddleware(lambda req: HttpResponse("ok"))
    response = middleware(request)

    assert response.status_code == 403
    assert json.loads(response.content)["error"] == "IP temporarily banned"


@pytest.mark.django_db
def test_apigate_blocks_missing_js_token(monkeypatch):
    rf = RequestFactory()
    request = rf.get("/api/search/countries")
    request.client_ip = "127.0.0.1"
    request.client_ua = "ua"

    monkeypatch.setattr("apps.security.middleware.is_ip_banned", lambda _ip: False)
    monkeypatch.setattr("apps.security.middleware.validate_js_gate_token", lambda **kwargs: False)

    middleware = ApiGateMiddleware(lambda req: HttpResponse("ok"))
    response = middleware(request)

    assert response.status_code == 403
    assert "invalid JS gate token" in json.loads(response.content)["error"]


@pytest.mark.django_db
def test_apigate_sets_csp_header(monkeypatch):
    rf = RequestFactory()
    request = rf.get("/dashboard/")
    request.client_ip = "127.0.0.1"
    request.client_ua = "ua"

    monkeypatch.setattr("apps.security.middleware.is_ip_banned", lambda _ip: False)

    middleware = ApiGateMiddleware(lambda req: HttpResponse("ok"))
    response = middleware(request)

    assert response.status_code == 200
    assert "Content-Security-Policy" in response

from __future__ import annotations

import pytest
from django.test import RequestFactory, override_settings

from app.env import env_bool, env_int, env_list, env_str
from apps.common.context_processors import global_flags


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1", True),
        ("true", True),
        ("YES", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("off", False),
    ],
)
def test_env_bool_parsing(monkeypatch, raw, expected):
    monkeypatch.setenv("BOOL_EXAMPLE", raw)

    assert env_bool("BOOL_EXAMPLE") is expected


def test_env_str_and_env_int_defaults(monkeypatch):
    monkeypatch.delenv("STRING_EXAMPLE", raising=False)
    monkeypatch.delenv("INT_EXAMPLE", raising=False)

    assert env_str("STRING_EXAMPLE", "fallback") == "fallback"
    assert env_int("INT_EXAMPLE", 99) == 99


def test_env_int_invalid_value_returns_default(monkeypatch):
    monkeypatch.setenv("INT_EXAMPLE", "abc")

    assert env_int("INT_EXAMPLE", 42) == 42


def test_env_list_parsing_and_default(monkeypatch):
    monkeypatch.setenv("LIST_EXAMPLE", " de, en ,, fr ")
    monkeypatch.delenv("LIST_EMPTY", raising=False)

    assert env_list("LIST_EXAMPLE") == ["de", "en", "fr"]
    assert env_list("LIST_EMPTY", ["fallback"]) == ["fallback"]


@override_settings(
    APP_PUBLIC_URL="https://truelens.example.test",
    PROJECT_NAME="TrueLens",
    SEARCH_STEP_TIMEOUT_SECONDS=45,
    PROFILE_VIEW_WINDOW_SECONDS=240,
)
def test_global_flags_context_processor_uses_settings_values():
    request = RequestFactory().get("/")

    context = global_flags(request)

    assert context == {
        "APP_PUBLIC_URL": "https://truelens.example.test",
        "PROJECT_NAME": "TrueLens",
        "SEARCH_STEP_TIMEOUT_SECONDS": 45,
        "PROFILE_VIEW_WINDOW_SECONDS": 240,
    }

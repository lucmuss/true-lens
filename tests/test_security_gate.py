import pytest

from apps.security.services import create_js_gate_token, validate_js_gate_token


@pytest.mark.django_db
def test_js_gate_token_tied_to_ip_and_user_agent():
    token = create_js_gate_token(ip="10.0.0.5", user_agent="pytest-agent")
    assert validate_js_gate_token(token=token, ip="10.0.0.5", user_agent="pytest-agent") is True
    assert validate_js_gate_token(token=token, ip="10.0.0.6", user_agent="pytest-agent") is False
    assert validate_js_gate_token(token=token, ip="10.0.0.5", user_agent="other-agent") is False

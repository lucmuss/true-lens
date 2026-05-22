from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class CaptchaChallenge(models.Model):
    captcha_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    code_digest = models.CharField(max_length=64)
    salt = models.CharField(max_length=32)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    expires_at = models.DateTimeField()
    solved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "security_captcha_challenge"
        indexes = [models.Index(fields=["captcha_id"]), models.Index(fields=["expires_at"])]


class ApiGateToken(models.Model):
    token = models.CharField(max_length=512, unique=True)
    ip = models.GenericIPAddressField()
    user_agent_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    rotation_counter = models.PositiveIntegerField(default=0)
    last_seen_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "security_api_gate_token"
        indexes = [models.Index(fields=["ip", "expires_at"])]


class IPBan(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=255)
    strike_count = models.PositiveIntegerField(default=0)
    banned_until = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "security_ip_ban"
        indexes = [models.Index(fields=["banned_until"])]


class SecurityEvent(models.Model):
    class EventType(models.TextChoices):
        CAPTCHA_FAILED = "captcha_failed", "Captcha Failed"
        CAPTCHA_SOLVED = "captcha_solved", "Captcha Solved"
        API_GATE_FAILED = "api_gate_failed", "API Gate Failed"
        API_GATE_PASSED = "api_gate_passed", "API Gate Passed"
        LOOKUP_TIMEOUT = "lookup_timeout", "Lookup Timeout"
        RATE_LIMIT = "rate_limit", "Rate Limit"
        IP_BANNED = "ip_banned", "IP Banned"

    event_type = models.CharField(max_length=32, choices=EventType.choices)
    ip = models.GenericIPAddressField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "security_event"
        indexes = [models.Index(fields=["event_type", "created_at"]), models.Index(fields=["ip", "created_at"])]

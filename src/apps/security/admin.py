from django.contrib import admin

from .models import ApiGateToken, CaptchaChallenge, IPBan, SecurityEvent


@admin.register(CaptchaChallenge)
class CaptchaChallengeAdmin(admin.ModelAdmin):
    list_display = ("captcha_id", "attempts", "expires_at", "solved_at", "created_at")
    search_fields = ("captcha_id",)


@admin.register(ApiGateToken)
class ApiGateTokenAdmin(admin.ModelAdmin):
    list_display = ("ip", "expires_at", "rotation_counter", "created_at")
    search_fields = ("ip", "token")


@admin.register(IPBan)
class IPBanAdmin(admin.ModelAdmin):
    list_display = ("ip", "reason", "strike_count", "banned_until", "updated_at")
    search_fields = ("ip", "reason")


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "ip", "user", "created_at")
    list_filter = ("event_type",)
    search_fields = ("ip",)

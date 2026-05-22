from django.contrib import admin

from .models import (
    Candidate,
    CandidateAttributeDefinition,
    CandidateAttributeVote,
    CandidateViewLog,
    LookupAttempt,
    LookupSession,
)


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "gender", "country", "region", "city", "profile_views_count")
    list_filter = ("gender", "hair_color", "country")
    search_fields = ("first_name", "last_name", "primary_email", "primary_phone", "city")


@admin.register(CandidateAttributeDefinition)
class CandidateAttributeDefinitionAdmin(admin.ModelAdmin):
    list_display = ("code", "slug", "label", "icon", "is_active")
    list_filter = ("is_active",)


@admin.register(CandidateAttributeVote)
class CandidateAttributeVoteAdmin(admin.ModelAdmin):
    list_display = ("candidate", "attribute", "recruiter", "is_anonymous", "voted_on", "is_visible")
    list_filter = ("is_anonymous", "is_visible", "voted_on")
    search_fields = ("candidate__first_name", "candidate__last_name", "recruiter__email")


@admin.register(CandidateViewLog)
class CandidateViewLogAdmin(admin.ModelAdmin):
    list_display = ("candidate", "recruiter", "ip", "viewed_at")
    search_fields = ("candidate__first_name", "candidate__last_name", "ip")


@admin.register(LookupSession)
class LookupSessionAdmin(admin.ModelAdmin):
    list_display = ("token", "requester", "requester_ip", "case_type", "status", "current_step", "created_at")
    list_filter = ("status", "case_type")
    search_fields = ("token", "requester__email", "requester_ip")


@admin.register(LookupAttempt)
class LookupAttemptAdmin(admin.ModelAdmin):
    list_display = ("session", "step", "ip", "success", "reason", "created_at")
    list_filter = ("success", "step")
    search_fields = ("ip", "reason")

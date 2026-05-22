from django.contrib import admin

from .models import DataEnrichmentSubmission, SupporterNodeApplication


@admin.register(DataEnrichmentSubmission)
class DataEnrichmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("candidate", "recruiter", "status", "created_at", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("candidate__first_name", "candidate__last_name", "recruiter__email")


@admin.register(SupporterNodeApplication)
class SupporterNodeApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant_name", "applicant_email", "base_url", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("applicant_name", "applicant_email", "base_url")

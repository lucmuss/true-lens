from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import RecruiterContactRelay, RecruiterSecurityVerification, RecruiterUser


@admin.register(RecruiterUser)
class RecruiterUserAdmin(UserAdmin):
    model = RecruiterUser
    ordering = ("email",)
    list_display = ("email", "is_staff", "is_verified_recruiter", "credits", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_active", "is_verified_recruiter")
    search_fields = ("email", "display_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {
                "fields": (
                    "display_name",
                    "credits",
                    "is_verified_recruiter",
                    "notify_on_vote_overlap",
                    "notify_on_contact_requests",
                    "notify_on_security",
                )
            },
        ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "deleted_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )


@admin.register(RecruiterSecurityVerification)
class RecruiterSecurityVerificationAdmin(admin.ModelAdmin):
    list_display = ("recruiter", "token", "is_completed", "expires_at", "created_at")
    list_filter = ("is_completed",)
    search_fields = ("recruiter__email", "token")


@admin.register(RecruiterContactRelay)
class RecruiterContactRelayAdmin(admin.ModelAdmin):
    list_display = ("initiator", "target", "candidate_id", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("initiator__email", "target__email", "candidate_id")

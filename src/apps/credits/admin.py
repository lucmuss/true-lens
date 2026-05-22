from django.contrib import admin

from .models import CreditLedgerEntry, CreditPurchase


@admin.register(CreditLedgerEntry)
class CreditLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("recruiter", "entry_type", "delta", "reason", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("recruiter__email", "reason")


@admin.register(CreditPurchase)
class CreditPurchaseAdmin(admin.ModelAdmin):
    list_display = ("recruiter", "credits_purchased", "amount_paid", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("recruiter__email", "stripe_session_id", "stripe_payment_intent_id")

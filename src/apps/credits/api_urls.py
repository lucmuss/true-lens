from django.urls import path

from . import api_views

urlpatterns = [
    path("credits/checkout", api_views.credit_checkout, name="api_credit_checkout"),
    path("credits/webhook/stripe", api_views.stripe_webhook, name="api_stripe_webhook"),
    path("credits/wallet", api_views.wallet, name="api_wallet"),
]

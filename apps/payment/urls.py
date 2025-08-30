# apps/payment/urls.py (simplified - webhook only)
from django.urls import path
from . import views

urlpatterns = [
    path("webhook/", views.stripe_webhook, name="stripe-webhook"),
]
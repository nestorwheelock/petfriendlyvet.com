"""API URL configuration for billing app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]

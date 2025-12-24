"""API URL configuration for delivery driver endpoints."""
from django.urls import path

from .api_views import (
    DriverDeliveriesView,
    DriverDeliveryDetailView,
    DriverUpdateStatusView,
)

app_name = 'delivery_api'

urlpatterns = [
    path('deliveries/', DriverDeliveriesView.as_view(), name='driver_deliveries'),
    path('deliveries/<int:delivery_id>/', DriverDeliveryDetailView.as_view(), name='driver_delivery_detail'),
    path('deliveries/<int:delivery_id>/status/', DriverUpdateStatusView.as_view(), name='driver_update_status'),
]

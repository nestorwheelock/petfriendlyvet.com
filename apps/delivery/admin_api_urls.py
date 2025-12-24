"""Admin API URL configuration for delivery management."""
from django.urls import path

from .admin_views import (
    AdminDeliveriesAPIView,
    AdminDriversAPIView,
    AdminAssignDriverView,
    AdminReportsAPIView,
    AdminDriverReportAPIView,
    AdminZonesAPIView,
    AdminZoneDetailAPIView,
    AdminSlotsAPIView,
    AdminSlotDetailAPIView,
    AdminSlotsBulkCreateAPIView,
    AdminContractorsAPIView,
    AdminContractorDetailAPIView,
    ValidateRFCAPIView,
    ValidateCURPAPIView,
    ContractorPaymentsAPIView,
    ContractorPaymentDetailAPIView,
)

app_name = 'delivery_admin_api'

urlpatterns = [
    path('deliveries/', AdminDeliveriesAPIView.as_view(), name='deliveries'),
    path('drivers/', AdminDriversAPIView.as_view(), name='drivers'),
    path('assign/<int:delivery_id>/', AdminAssignDriverView.as_view(), name='assign'),
    path('reports/', AdminReportsAPIView.as_view(), name='reports'),
    path('reports/driver/<int:driver_id>/', AdminDriverReportAPIView.as_view(), name='driver_report'),
    path('zones/', AdminZonesAPIView.as_view(), name='zones'),
    path('zones/<int:zone_id>/', AdminZoneDetailAPIView.as_view(), name='zone_detail'),
    path('slots/', AdminSlotsAPIView.as_view(), name='slots'),
    path('slots/<int:slot_id>/', AdminSlotDetailAPIView.as_view(), name='slot_detail'),
    path('slots/bulk/', AdminSlotsBulkCreateAPIView.as_view(), name='slots_bulk'),
    path('contractors/', AdminContractorsAPIView.as_view(), name='contractors'),
    path('contractors/<int:contractor_id>/', AdminContractorDetailAPIView.as_view(), name='contractor_detail'),
    path('contractors/validate-rfc/', ValidateRFCAPIView.as_view(), name='validate_rfc'),
    path('contractors/validate-curp/', ValidateCURPAPIView.as_view(), name='validate_curp'),
    path('contractors/payments/', ContractorPaymentsAPIView.as_view(), name='contractor_payments'),
    path('contractors/<int:contractor_id>/payments/', ContractorPaymentDetailAPIView.as_view(), name='contractor_payment_detail'),
]

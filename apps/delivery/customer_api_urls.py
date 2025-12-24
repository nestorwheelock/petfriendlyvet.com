"""Customer-facing API URL configuration for delivery."""
from django.urls import path

from .customer_api_views import (
    AvailableSlotsView,
    AvailableDatesView,
    DeliveryZonesView,
    DeliveryTrackingAPIView,
    DeliveryRatingAPIView,
)

app_name = 'delivery_customer_api'

urlpatterns = [
    path('slots/', AvailableSlotsView.as_view(), name='available_slots'),
    path('slots/dates/', AvailableDatesView.as_view(), name='available_dates'),
    path('zones/', DeliveryZonesView.as_view(), name='delivery_zones'),
    path('track/<str:delivery_number>/', DeliveryTrackingAPIView.as_view(), name='tracking_api'),
    path('rate/<str:delivery_number>/', DeliveryRatingAPIView.as_view(), name='rating_api'),
]

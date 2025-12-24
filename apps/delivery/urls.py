"""URL configuration for the delivery app."""
from django.urls import path

from .views import DriverDashboardView

app_name = 'delivery'

urlpatterns = [
    # Driver-facing URLs
    path('driver/dashboard/', DriverDashboardView.as_view(), name='driver_dashboard'),

    # Customer-facing URLs will be added here
    # e.g., tracking page, rating form
]

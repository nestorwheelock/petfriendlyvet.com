"""URL configuration for the delivery app."""
from django.urls import path, include

from .views import DriverDashboardView, DeliveryTrackingView
from .admin_views import AdminDashboardView

app_name = 'delivery'

urlpatterns = [
    # Driver-facing URLs
    path('driver/dashboard/', DriverDashboardView.as_view(), name='driver_dashboard'),

    # Customer-facing URLs
    path('track/<str:delivery_number>/', DeliveryTrackingView.as_view(), name='tracking'),

    # Admin URLs
    path('admin/', include('apps.delivery.admin_urls')),
]

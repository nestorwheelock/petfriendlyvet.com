"""URL configuration for the delivery app."""
from django.urls import path, include
from django.views.generic import RedirectView

from .views import DriverDashboardView, DeliveryTrackingView
from .admin_views import AdminDashboardView

app_name = 'delivery'

urlpatterns = [
    # Root redirect to driver dashboard
    path('', RedirectView.as_view(pattern_name='delivery:driver_dashboard'), name='index'),

    # Driver-facing URLs
    path('driver/dashboard/', DriverDashboardView.as_view(), name='driver_dashboard'),

    # Customer-facing URLs
    path('track/<str:delivery_number>/', DeliveryTrackingView.as_view(), name='tracking'),

    # Admin URLs
    path('admin/', include('apps.delivery.admin_urls')),
]

"""URL configuration for the delivery app."""
from django.urls import path, include
from django.views.generic import RedirectView

from .views import DriverDashboardView, DeliveryTrackingView
from .admin_views import AdminDashboardView, ZonesView

app_name = 'delivery'

urlpatterns = [
    # Root redirect to admin dashboard (staff) or driver dashboard
    path('', RedirectView.as_view(pattern_name='delivery:delivery_admin:dashboard'), name='index'),

    # Direct access shortcuts for common admin pages
    path('zones/', ZonesView.as_view(), name='zones'),

    # Driver-facing URLs
    path('driver/dashboard/', DriverDashboardView.as_view(), name='driver_dashboard'),

    # Customer-facing URLs
    path('track/<str:delivery_number>/', DeliveryTrackingView.as_view(), name='tracking'),

    # Admin URLs
    path('admin/', include('apps.delivery.admin_urls')),
]

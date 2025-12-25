"""Admin URL configuration for delivery management."""
from django.urls import path
from django.views.generic import RedirectView

from .admin_views import (
    AdminDashboardView,
    ReportsView,
    ZonesView,
    SlotsView,
    ContractorsView,
)

app_name = 'delivery_admin'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='delivery:delivery_admin:dashboard'), name='index'),
    path('dashboard/', AdminDashboardView.as_view(), name='dashboard'),
    path('reports/', ReportsView.as_view(), name='reports'),
    path('zones/', ZonesView.as_view(), name='zones'),
    path('slots/', SlotsView.as_view(), name='slots'),
    path('contractors/', ContractorsView.as_view(), name='contractors'),
]

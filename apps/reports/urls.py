"""URL configuration for the reports app."""
from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsDashboardView.as_view(), name='dashboard'),
    path('sales/', views.SalesReportView.as_view(), name='sales'),
    path('appointments/', views.AppointmentsReportView.as_view(), name='appointments'),
    path('inventory/', views.InventoryReportView.as_view(), name='inventory'),
    path('customers/', views.CustomersReportView.as_view(), name='customers'),
]

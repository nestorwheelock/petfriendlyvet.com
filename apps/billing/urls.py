"""URL configuration for billing app."""
from django.urls import path

from . import views

app_name = 'billing'

urlpatterns = [
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('credit/', views.CreditBalanceView.as_view(), name='credit_balance'),
]

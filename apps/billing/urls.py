"""URL configuration for billing app."""
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'billing'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='billing:invoice_list'), name='index'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('credit/', views.CreditBalanceView.as_view(), name='credit_balance'),
]

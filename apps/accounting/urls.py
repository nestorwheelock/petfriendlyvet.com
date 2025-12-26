"""URL configuration for accounting app."""
from django.urls import path

from . import views

app_name = 'accounting'

urlpatterns = [
    path('', views.AccountingDashboardView.as_view(), name='dashboard'),
    path('accounts/', views.AccountListView.as_view(), name='account_list'),
    path('accounts/add/', views.AccountCreateView.as_view(), name='account_create'),
    path('accounts/<int:pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('accounts/<int:pk>/edit/', views.AccountUpdateView.as_view(), name='account_update'),
    path('accounts/<int:pk>/delete/', views.AccountDeleteView.as_view(), name='account_delete'),
    path('journals/', views.JournalListView.as_view(), name='journal_list'),
    path('journals/<int:pk>/', views.JournalDetailView.as_view(), name='journal_detail'),
    path('vendors/', views.VendorListView.as_view(), name='vendor_list'),
    path('vendors/<int:pk>/', views.VendorDetailView.as_view(), name='vendor_detail'),
    path('bills/', views.BillListView.as_view(), name='bill_list'),
    path('bills/<int:pk>/', views.BillDetailView.as_view(), name='bill_detail'),
    path('budgets/', views.BudgetListView.as_view(), name='budget_list'),
    path('reconciliations/', views.ReconciliationListView.as_view(), name='reconciliation_list'),
    path('reconciliations/<int:pk>/', views.ReconciliationDetailView.as_view(), name='reconciliation_detail'),
]

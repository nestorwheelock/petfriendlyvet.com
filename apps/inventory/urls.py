"""Inventory app URL patterns."""
from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('stock/', views.stock_levels, name='stock_levels'),
    path('batches/', views.batch_list, name='batches'),
    path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),
    path('movements/', views.movement_list, name='movements'),
    path('movements/add/', views.movement_add, name='movement_add'),
    path('suppliers/', views.supplier_list, name='suppliers'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('purchase-orders/', views.purchase_order_list, name='purchase_orders'),
    path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('alerts/', views.alerts, name='alerts'),
    path('expiring/', views.expiring_items, name='expiring'),
]

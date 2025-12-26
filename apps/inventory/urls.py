"""Inventory app URL patterns."""
from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Stock Levels
    path('stock/', views.stock_levels, name='stock_levels'),
    path('stock/', views.stock_levels, name='stock'),  # Alias
    path('stock/add/', views.stock_level_create, name='stock_level_create'),
    path('stock/<int:pk>/edit/', views.stock_level_edit, name='stock_level_edit'),
    path('stock/<int:pk>/adjust/', views.stock_level_adjust, name='stock_level_adjust'),

    # Batches
    path('batches/', views.batch_list, name='batches'),
    path('batches/add/', views.batch_create, name='batch_create'),
    path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:pk>/edit/', views.batch_edit, name='batch_edit'),

    # Stock Movements
    path('movements/', views.movement_list, name='movements'),
    path('movements/add/', views.movement_add, name='movement_add'),

    # Suppliers
    path('suppliers/', views.supplier_list, name='suppliers'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),

    # Stock Locations
    path('locations/', views.stock_location_list, name='locations'),
    path('locations/add/', views.stock_location_create, name='location_create'),
    path('locations/<int:pk>/edit/', views.stock_location_edit, name='location_edit'),

    # Location Types
    path('location-types/', views.location_type_list, name='location_types'),
    path('location-types/add/', views.location_type_create, name='location_type_create'),
    path('location-types/<int:pk>/edit/', views.location_type_edit, name='location_type_edit'),
    path('location-types/<int:pk>/delete/', views.location_type_delete, name='location_type_delete'),

    # Purchase Orders
    path('purchase-orders/', views.purchase_order_list, name='purchase_orders'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/edit/', views.purchase_order_edit, name='purchase_order_edit'),
    path('purchase-orders/<int:pk>/submit/', views.purchase_order_submit, name='purchase_order_submit'),
    path('purchase-orders/<int:pk>/receive/', views.purchase_order_receive, name='purchase_order_receive'),
    path('purchase-orders/<int:po_pk>/lines/add/', views.po_line_add, name='po_line_add'),
    path('purchase-orders/<int:po_pk>/lines/<int:pk>/edit/', views.po_line_edit, name='po_line_edit'),
    path('purchase-orders/<int:po_pk>/lines/<int:pk>/delete/', views.po_line_delete, name='po_line_delete'),

    # Reorder Rules
    path('reorder-rules/', views.reorder_rule_list, name='reorder_rules'),
    path('reorder-rules/add/', views.reorder_rule_create, name='reorder_rule_create'),
    path('reorder-rules/<int:pk>/edit/', views.reorder_rule_edit, name='reorder_rule_edit'),

    # Product-Supplier Links
    path('product-suppliers/', views.product_supplier_list, name='product_suppliers'),
    path('product-suppliers/add/', views.product_supplier_create, name='product_supplier_create'),
    path('product-suppliers/<int:pk>/edit/', views.product_supplier_edit, name='product_supplier_edit'),

    # Stock Counts
    path('stock-counts/', views.stock_count_list, name='stock_counts'),
    path('stock-counts/create/', views.stock_count_create, name='stock_count_create'),
    path('stock-counts/<int:pk>/', views.stock_count_detail, name='stock_count_detail'),
    path('stock-counts/<int:pk>/entry/', views.stock_count_entry, name='stock_count_entry'),
    path('stock-counts/<int:pk>/approve/', views.stock_count_approve, name='stock_count_approve'),

    # Transfers
    path('transfers/create/', views.transfer_create, name='transfer_create'),

    # Alerts
    path('alerts/', views.alerts, name='alerts'),
    path('expiring/', views.expiring_items, name='expiring'),
]

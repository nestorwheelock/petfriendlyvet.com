"""Practice management URL patterns."""
from django.urls import path

from . import views

app_name = 'practice'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),

    # Schedule
    path('schedule/', views.schedule, name='schedule'),
    path('shifts/', views.shift_list, name='shift_list'),

    # Time Tracking
    path('time/', views.time_tracking, name='time_tracking'),

    # Tasks
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),

    # Procedure Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Procedures
    path('procedures/', views.procedure_list, name='procedure_list'),
    path('procedures/add/', views.procedure_create, name='procedure_create'),
    path('procedures/<int:pk>/edit/', views.procedure_edit, name='procedure_edit'),
    path('procedures/<int:pk>/delete/', views.procedure_delete, name='procedure_delete'),

    # Procedure Providers (qualified staff who can perform procedure)
    path('procedures/<int:pk>/providers/', views.procedure_providers, name='procedure_providers'),
    path('procedures/<int:pk>/providers/add/', views.procedure_add_provider, name='procedure_add_provider'),
    path('procedures/<int:pk>/providers/remove/', views.procedure_remove_provider, name='procedure_remove_provider'),

    # Procedure Consumables (inventory items consumed during procedure)
    path('procedures/<int:pk>/consumables/', views.procedure_consumables, name='procedure_consumables'),
    path('procedures/<int:pk>/consumables/add/', views.procedure_add_consumable, name='procedure_add_consumable'),
    path('procedures/<int:pk>/consumables/<int:consumable_pk>/update/', views.procedure_update_consumable, name='procedure_update_consumable'),
    path('procedures/<int:pk>/consumables/<int:consumable_pk>/remove/', views.procedure_remove_consumable, name='procedure_remove_consumable'),

    # Settings
    path('settings/', views.clinic_settings, name='clinic_settings'),
]

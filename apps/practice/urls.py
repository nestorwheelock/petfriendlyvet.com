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

    # Settings
    path('settings/', views.clinic_settings, name='clinic_settings'),
]

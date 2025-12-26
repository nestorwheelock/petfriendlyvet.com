"""URL configuration for superadmin app."""

from django.urls import path

from . import views

app_name = 'superadmin'

urlpatterns = [
    # Dashboard
    path('', views.SuperadminDashboardView.as_view(), name='dashboard'),

    # User Management
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/deactivate/', views.UserDeactivateView.as_view(), name='user_deactivate'),

    # Roles
    path('roles/', views.RoleListView.as_view(), name='role_list'),

    # Module Management
    path('modules/', views.ModuleListView.as_view(), name='module_list'),
    path('modules/<int:pk>/toggle/', views.ModuleToggleView.as_view(), name='module_toggle'),
    path('modules/<int:pk>/features/', views.ModuleFeaturesView.as_view(), name='module_features'),

    # Feature Flags
    path('features/<int:pk>/toggle/', views.FeatureToggleView.as_view(), name='feature_toggle'),

    # Settings
    path('settings/', views.SettingsView.as_view(), name='settings'),

    # Audit
    path('audit/', views.AuditDashboardView.as_view(), name='audit_dashboard'),

    # Monitoring
    path('monitoring/', views.MonitoringView.as_view(), name='monitoring'),
]

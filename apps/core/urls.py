"""Core URL configuration."""
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', views.ServicesView.as_view(), name='services'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('staff/', views.StaffHubView.as_view(), name='staff_hub'),
    path('portal/', views.PortalDashboardView.as_view(), name='portal_dashboard'),
]

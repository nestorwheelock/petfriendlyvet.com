"""Referral network URL patterns."""
from django.urls import path

from . import views

app_name = 'referrals'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Specialists Directory
    path('specialists/', views.specialist_list, name='specialist_list'),
    path('specialists/<int:pk>/', views.specialist_detail, name='specialist_detail'),

    # Referrals
    path('outbound/', views.referral_list, name='referral_list'),
    path('outbound/<int:pk>/', views.referral_detail, name='referral_detail'),

    # Visiting Specialists
    path('visiting/', views.visiting_schedule, name='visiting_schedule'),
    path('visiting/<int:pk>/', views.visiting_detail, name='visiting_detail'),
]

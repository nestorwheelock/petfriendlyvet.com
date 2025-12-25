"""Loyalty app URL patterns."""
from django.urls import path

from . import views

app_name = 'loyalty'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('rewards/', views.rewards_catalog, name='rewards'),
    path('rewards/<int:pk>/redeem/', views.redeem_reward, name='redeem'),
    path('history/', views.transaction_history, name='history'),
    path('tiers/', views.tier_benefits, name='tiers'),
    path('referrals/', views.referral_program, name='referrals'),
]

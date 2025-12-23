"""URL patterns for services app."""
from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    # Partner directory
    path('partners/', views.PartnerListView.as_view(), name='partner_list'),
    path('partners/<int:pk>/', views.PartnerDetailView.as_view(), name='partner_detail'),

    # Referrals
    path('partners/<int:partner_pk>/refer/', views.ReferralCreateView.as_view(), name='referral_create'),
    path('referrals/', views.ReferralListView.as_view(), name='referral_list'),
]

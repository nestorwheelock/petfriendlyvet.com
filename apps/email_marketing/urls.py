"""URL configuration for email marketing app."""
from django.urls import path

from . import views

app_name = 'marketing'

urlpatterns = [
    path('', views.MarketingDashboardView.as_view(), name='dashboard'),
    path('campaigns/', views.CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='campaign_detail'),
    path('subscribers/', views.SubscriberListView.as_view(), name='subscriber_list'),
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('segments/', views.SegmentListView.as_view(), name='segment_list'),
    path('sequences/', views.SequenceListView.as_view(), name='sequence_list'),
]

"""URL patterns for travel app."""
from django.urls import path

from . import views

app_name = 'travel'

urlpatterns = [
    # Destinations
    path('destinations/', views.DestinationListView.as_view(), name='destination_list'),
    path('destinations/<int:pk>/', views.DestinationDetailView.as_view(), name='destination_detail'),

    # Health Certificates
    path('certificates/', views.CertificateListView.as_view(), name='certificate_list'),
    path('certificates/<int:pk>/', views.CertificateDetailView.as_view(), name='certificate_detail'),
    path('certificates/request/<int:pet_pk>/', views.CertificateRequestView.as_view(), name='certificate_request'),

    # Travel Plans
    path('plans/', views.TravelPlanListView.as_view(), name='travel_plan_list'),
    path('plans/create/', views.TravelPlanCreateView.as_view(), name='travel_plan_create'),
]

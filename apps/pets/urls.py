"""URL patterns for pets app."""
from django.urls import path

from . import views

app_name = 'pets'

urlpatterns = [
    path('', views.OwnerDashboardView.as_view(), name='dashboard'),
    path('pets/', views.PetListView.as_view(), name='pet_list'),
    path('pets/add/', views.PetCreateView.as_view(), name='pet_add'),
    path('pets/<int:pk>/', views.PetDetailView.as_view(), name='pet_detail'),
    path('pets/<int:pk>/edit/', views.PetUpdateView.as_view(), name='pet_edit'),
]

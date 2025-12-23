"""URL patterns for pets app."""
from django.urls import path

from . import views
from . import document_views

app_name = 'pets'

urlpatterns = [
    path('', views.OwnerDashboardView.as_view(), name='dashboard'),
    path('pets/', views.PetListView.as_view(), name='pet_list'),
    path('pets/add/', views.PetCreateView.as_view(), name='pet_add'),
    path('pets/<int:pk>/', views.PetDetailView.as_view(), name='pet_detail'),
    path('pets/<int:pk>/edit/', views.PetUpdateView.as_view(), name='pet_edit'),

    # Document management
    path('pets/<int:pet_pk>/documents/', document_views.DocumentListView.as_view(), name='document_list'),
    path('pets/<int:pet_pk>/documents/upload/', document_views.DocumentUploadView.as_view(), name='document_upload'),
    path('pets/<int:pet_pk>/documents/<int:pk>/delete/', document_views.DocumentDeleteView.as_view(), name='document_delete'),
]

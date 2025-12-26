"""URL patterns for pets app."""
from django.urls import path

from . import views
from . import document_views

app_name = 'pets'

urlpatterns = [
    # Main views
    path('', views.OwnerDashboardView.as_view(), name='dashboard'),
    path('list/', views.PetListView.as_view(), name='pet_list'),
    path('add/', views.PetCreateView.as_view(), name='pet_add'),
    path('<int:pk>/', views.PetDetailView.as_view(), name='pet_detail'),
    path('<int:pk>/edit/', views.PetUpdateView.as_view(), name='pet_edit'),
    path('<int:pk>/archive/', views.PetArchiveView.as_view(), name='pet_archive'),
    path('<int:pk>/unarchive/', views.PetUnarchiveView.as_view(), name='pet_unarchive'),
    path('<int:pk>/mark-deceased/', views.PetMarkDeceasedView.as_view(), name='pet_mark_deceased'),

    # Document management
    path('<int:pet_pk>/documents/', document_views.DocumentListView.as_view(), name='document_list'),
    path('<int:pet_pk>/documents/upload/', document_views.DocumentUploadView.as_view(), name='document_upload'),
    path('<int:pet_pk>/documents/<int:pk>/delete/', document_views.DocumentDeleteView.as_view(), name='document_delete'),
]

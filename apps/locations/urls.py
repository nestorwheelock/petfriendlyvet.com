"""Location management URL patterns."""
from django.urls import path

from . import views

app_name = 'locations'

urlpatterns = [
    # Location list
    path('', views.location_list, name='location_list'),

    # Exam rooms for a location
    path('<int:location_id>/rooms/', views.room_list, name='room_list'),
    path('<int:location_id>/rooms/add/', views.room_create, name='room_create'),
    path('<int:location_id>/rooms/<int:room_id>/edit/', views.room_edit, name='room_edit'),
    path('<int:location_id>/rooms/<int:room_id>/deactivate/', views.room_deactivate, name='room_deactivate'),
    path('<int:location_id>/rooms/<int:room_id>/reactivate/', views.room_reactivate, name='room_reactivate'),
]

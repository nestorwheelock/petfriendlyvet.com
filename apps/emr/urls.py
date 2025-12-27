"""EMR URL configuration for Staff Panel → Clinical section.

Routes:
    /                           → Whiteboard (encounter board by pipeline state)
    /select-location/           → POST to set session location
    /patients/<id>/             → Patient clinical summary
    /encounters/<id>/transition/ → POST state transition (HTMX-friendly)
"""
from django.urls import path

from . import views

app_name = 'emr'

urlpatterns = [
    # Whiteboard - encounter board filtered by location
    path('', views.whiteboard, name='whiteboard'),

    # Location selector - POST to set session
    path('select-location/', views.select_location, name='select_location'),

    # Patient clinical summary
    path('patients/<int:patient_id>/', views.patient_summary, name='patient_summary'),

    # Encounter state transition (HTMX POST)
    path(
        'encounters/<int:encounter_id>/transition/',
        views.transition_encounter,
        name='transition_encounter',
    ),
]

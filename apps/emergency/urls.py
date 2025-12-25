"""Emergency app URL patterns."""
from django.urls import path

from . import views

app_name = 'emergency'

urlpatterns = [
    path('', views.emergency_home, name='home'),
    path('triage/', views.triage_form, name='triage'),
    path('triage/result/', views.triage_result, name='triage_result'),
    path('first-aid/', views.first_aid_list, name='first_aid_list'),
    path('first-aid/<int:pk>/', views.first_aid_detail, name='first_aid_detail'),
    path('hospitals/', views.hospital_list, name='hospitals'),
    path('contact/', views.emergency_contact, name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),
    path('history/', views.emergency_history, name='history'),
]

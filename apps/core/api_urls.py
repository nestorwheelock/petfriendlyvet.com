"""Core API URL configuration."""
from django.urls import path, include

app_name = 'api'

urlpatterns = [
    path('v1/auth/', include('apps.accounts.api_urls')),
    path('v1/pets/', include('apps.pets.api_urls')),
    path('v1/appointments/', include('apps.appointments.api_urls')),
    path('v1/store/', include('apps.store.api_urls')),
    path('v1/chat/', include('apps.ai_assistant.api_urls')),
]

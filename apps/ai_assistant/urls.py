from django.urls import path

from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('quick-actions/', views.get_quick_actions, name='quick_actions'),
    path('history/', views.get_chat_history, name='chat_history'),
]

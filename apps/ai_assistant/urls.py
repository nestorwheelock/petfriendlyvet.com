from django.urls import path

from . import views

app_name = 'ai_assistant'

urlpatterns = [
    # Customer chat
    path('', views.chat_view, name='chat'),
    path('quick-actions/', views.get_quick_actions, name='quick_actions'),
    path('history/', views.get_chat_history, name='chat_history'),

    # Admin chat
    path('admin/', views.admin_chat_view, name='admin_chat'),
    path('admin/api/', views.admin_chat_api_view, name='admin_chat_api'),
    path('admin/conversations/', views.conversation_list, name='conversation_list'),
]

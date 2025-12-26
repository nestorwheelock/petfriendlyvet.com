"""Account URL configuration."""
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('profile/change-email/', views.EmailChangeRequestView.as_view(), name='email_change'),
    path('profile/change-email/sent/', views.EmailChangeSentView.as_view(), name='email_change_sent'),
    path('profile/change-email/confirm/<str:token>/', views.EmailChangeConfirmView.as_view(), name='email_change_confirm'),
    path('profile/delete/', views.DeleteAccountView.as_view(), name='delete_account'),

    # Password reset
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/sent/', views.PasswordResetSentView.as_view(), name='password_reset_sent'),
    path('password-reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/invalid/', views.PasswordResetInvalidView.as_view(), name='password_reset_invalid'),
]

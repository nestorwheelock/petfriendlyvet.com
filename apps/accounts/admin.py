"""Account admin configuration."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin."""

    list_display = ['username', 'email', 'phone_number', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff', 'preferred_language']
    search_fields = ['username', 'email', 'phone_number', 'first_name', 'last_name']

    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Pet-Friendly Info'), {
            'fields': (
                'phone_number',
                'phone_verified',
                'email_verified',
                'preferred_language',
                'auth_method',
                'role',
                'avatar',
            )
        }),
        (_('Consent'), {
            'fields': ('marketing_consent', 'marketing_consent_date'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Pet-Friendly Info'), {
            'fields': ('email', 'phone_number', 'role'),
        }),
    )

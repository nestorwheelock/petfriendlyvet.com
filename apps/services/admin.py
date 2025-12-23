"""Admin configuration for external services."""
from django.contrib import admin

from .models import ExternalPartner, Referral


@admin.register(ExternalPartner)
class ExternalPartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'partner_type', 'phone', 'is_active', 'is_preferred', 'average_rating']
    list_filter = ['partner_type', 'is_active', 'is_preferred']
    search_fields = ['name', 'contact_name', 'email', 'phone']
    ordering = ['name']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['pet', 'partner', 'service_type', 'status', 'created_at']
    list_filter = ['status', 'service_type', 'partner']
    search_fields = ['pet__name', 'partner__name', 'referred_by__email']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

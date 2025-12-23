"""Admin configuration for travel certificates."""
from django.contrib import admin

from .models import TravelDestination, HealthCertificate, CertificateRequirement, TravelPlan


@admin.register(TravelDestination)
class TravelDestinationAdmin(admin.ModelAdmin):
    list_display = ['country_name', 'country_code', 'certificate_validity_days', 'quarantine_required', 'is_active']
    list_filter = ['is_active', 'quarantine_required']
    search_fields = ['country_name', 'country_code']
    ordering = ['country_name']


class CertificateRequirementInline(admin.TabularInline):
    model = CertificateRequirement
    extra = 0


@admin.register(HealthCertificate)
class HealthCertificateAdmin(admin.ModelAdmin):
    list_display = ['pet', 'destination', 'travel_date', 'status', 'issue_date', 'expiry_date']
    list_filter = ['status', 'destination']
    search_fields = ['pet__name', 'destination__country_name', 'certificate_number']
    date_hierarchy = 'travel_date'
    inlines = [CertificateRequirementInline]
    ordering = ['-created_at']


@admin.register(TravelPlan)
class TravelPlanAdmin(admin.ModelAdmin):
    list_display = ['pet', 'destination', 'departure_date', 'return_date', 'status']
    list_filter = ['status', 'destination']
    search_fields = ['pet__name', 'destination__country_name', 'airline', 'flight_number']
    date_hierarchy = 'departure_date'
    ordering = ['-departure_date']

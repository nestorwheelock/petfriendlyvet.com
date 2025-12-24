"""Admin configuration for pets app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Pet, MedicalCondition, Vaccination, Medication, WeightRecord, PetDocument


class MedicalConditionInline(admin.TabularInline):
    model = MedicalCondition
    extra = 0
    fields = ['condition_type', 'name', 'diagnosed_date', 'is_active']


class VaccinationInline(admin.TabularInline):
    model = Vaccination
    extra = 0
    fields = ['vaccine_name', 'date_administered', 'next_due_date', 'administered_by']
    ordering = ['-date_administered']


class MedicationInline(admin.TabularInline):
    model = Medication
    extra = 0
    fields = ['name', 'dosage', 'frequency', 'start_date', 'end_date']


class WeightRecordInline(admin.TabularInline):
    model = WeightRecord
    extra = 0
    fields = ['weight_kg', 'recorded_date', 'notes']
    readonly_fields = ['recorded_date']
    ordering = ['-recorded_date']
    max_num = 10


class PetDocumentInline(admin.TabularInline):
    model = PetDocument
    extra = 0
    fields = ['document_type', 'title', 'file', 'created_at']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'species_icon', 'breed', 'owner_link',
        'age_display', 'gender', 'is_neutered'
    ]
    list_filter = ['species', 'gender', 'is_neutered', 'created_at']
    search_fields = ['name', 'breed', 'microchip_id', 'owner__email', 'owner__first_name', 'owner__last_name']
    raw_id_fields = ['owner']
    date_hierarchy = 'created_at'
    ordering = ['name']
    inlines = [MedicalConditionInline, VaccinationInline, MedicationInline, WeightRecordInline, PetDocumentInline]

    fieldsets = (
        (None, {
            'fields': ('owner', 'name', 'photo')
        }),
        ('Basic Info', {
            'fields': ('species', 'breed', 'gender', 'date_of_birth')
        }),
        ('Physical', {
            'fields': ('weight_kg', 'is_neutered')
        }),
        ('Identification', {
            'fields': ('microchip_id',),
            'classes': ['collapse']
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Species')
    def species_icon(self, obj):
        icons = {
            'dog': '🐕',
            'cat': '🐱',
            'bird': '🐦',
            'rabbit': '🐰',
            'hamster': '🐹',
            'guinea_pig': '🐹',
            'reptile': '🦎',
            'other': '🐾',
        }
        icon = icons.get(obj.species, '🐾')
        return format_html('{} {}', icon, obj.get_species_display())

    @admin.display(description='Owner')
    def owner_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:accounts_user_change', args=[obj.owner.id])
        return format_html('<a href="{}">{}</a>', url, obj.owner.get_full_name() or obj.owner.email)

    @admin.display(description='Age')
    def age_display(self, obj):
        if obj.age_years is not None:
            if obj.age_years < 1:
                months = int(obj.age_years * 12)
                return f'{months} months'
            return f'{obj.age_years:.1f} years'
        return '-'


@admin.register(MedicalCondition)
class MedicalConditionAdmin(admin.ModelAdmin):
    list_display = ['pet', 'name', 'condition_type', 'is_active', 'diagnosed_date']
    list_filter = ['condition_type', 'is_active']
    search_fields = ['pet__name', 'name', 'notes']
    raw_id_fields = ['pet']


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ['pet', 'vaccine_name', 'date_administered', 'next_due_date', 'is_overdue_display']
    list_filter = ['vaccine_name', 'date_administered']
    search_fields = ['pet__name', 'vaccine_name']
    raw_id_fields = ['pet']
    date_hierarchy = 'date_administered'

    @admin.display(description='Overdue', boolean=True)
    def is_overdue_display(self, obj):
        return obj.is_overdue


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['pet', 'name', 'dosage', 'frequency', 'is_active_display', 'start_date', 'end_date']
    list_filter = ['start_date']
    search_fields = ['pet__name', 'name']
    raw_id_fields = ['pet']

    @admin.display(description='Active', boolean=True)
    def is_active_display(self, obj):
        return obj.is_active


@admin.register(WeightRecord)
class WeightRecordAdmin(admin.ModelAdmin):
    list_display = ['pet', 'weight_kg', 'recorded_date']
    list_filter = ['recorded_date']
    search_fields = ['pet__name']
    raw_id_fields = ['pet']
    date_hierarchy = 'recorded_date'


@admin.register(PetDocument)
class PetDocumentAdmin(admin.ModelAdmin):
    list_display = ['pet', 'document_type', 'title', 'created_at']
    list_filter = ['document_type', 'created_at']
    search_fields = ['pet__name', 'title']
    raw_id_fields = ['pet']
    date_hierarchy = 'created_at'

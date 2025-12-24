"""Django admin configuration for delivery models."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    DeliveryZone, DeliverySlot, DeliveryDriver,
    Delivery, DeliveryStatusHistory,
    DeliveryProof, DeliveryRating, DeliveryNotification
)


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    """Admin for delivery zones."""

    list_display = ['code', 'name', 'delivery_fee', 'estimated_time_minutes', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'name_es']
    list_editable = ['is_active']
    ordering = ['code']


@admin.register(DeliverySlot)
class DeliverySlotAdmin(admin.ModelAdmin):
    """Admin for delivery slots."""

    list_display = ['zone', 'date', 'start_time', 'end_time', 'capacity', 'booked_count', 'available', 'is_active']
    list_filter = ['zone', 'date', 'is_active']
    search_fields = ['zone__code', 'zone__name']
    date_hierarchy = 'date'
    ordering = ['date', 'start_time']

    def available(self, obj):
        """Show available capacity."""
        return obj.available_capacity
    available.short_description = 'Available'


@admin.register(DeliveryDriver)
class DeliveryDriverAdmin(admin.ModelAdmin):
    """Admin for delivery drivers."""

    list_display = ['user', 'driver_type', 'phone', 'vehicle_type', 'is_active', 'is_available', 'total_deliveries', 'average_rating']
    list_filter = ['driver_type', 'vehicle_type', 'is_active', 'is_available', 'zones']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone', 'rfc']
    list_editable = ['is_active', 'is_available']
    filter_horizontal = ['zones']
    readonly_fields = ['total_deliveries', 'successful_deliveries', 'average_rating', 'created_at', 'updated_at']

    fieldsets = [
        ('User Info', {
            'fields': ['user', 'driver_type', 'phone']
        }),
        ('Vehicle', {
            'fields': ['vehicle_type', 'license_plate']
        }),
        ('Zones', {
            'fields': ['zones']
        }),
        ('Contractor Info', {
            'fields': ['rfc', 'curp', 'rate_per_delivery', 'rate_per_km', 'contract_signed', 'contract_document', 'id_document'],
            'classes': ['collapse']
        }),
        ('Status', {
            'fields': ['is_active', 'is_available']
        }),
        ('Performance', {
            'fields': ['total_deliveries', 'successful_deliveries', 'average_rating']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


class DeliveryStatusHistoryInline(admin.TabularInline):
    """Inline for delivery status history."""

    model = DeliveryStatusHistory
    extra = 0
    readonly_fields = ['from_status', 'to_status', 'changed_by', 'latitude', 'longitude', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class DeliveryProofInline(admin.TabularInline):
    """Inline for delivery proofs."""

    model = DeliveryProof
    extra = 0
    readonly_fields = ['proof_type', 'recipient_name', 'latitude', 'longitude', 'gps_accuracy', 'created_at']


class DeliveryNotificationInline(admin.TabularInline):
    """Inline for delivery notifications."""

    model = DeliveryNotification
    extra = 0
    readonly_fields = ['notification_type', 'recipient', 'status', 'sent_at', 'delivered_at', 'created_at']


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """Admin for deliveries."""

    list_display = ['delivery_number', 'order', 'driver', 'zone', 'status', 'status_badge', 'scheduled_date', 'created_at']
    list_filter = ['status', 'zone', 'driver', 'scheduled_date']
    search_fields = ['delivery_number', 'order__order_number', 'address']
    date_hierarchy = 'created_at'
    raw_id_fields = ['order', 'driver', 'slot']
    readonly_fields = ['delivery_number', 'assigned_at', 'picked_up_at', 'out_for_delivery_at', 'arrived_at', 'delivered_at', 'failed_at', 'created_at', 'updated_at']
    inlines = [DeliveryStatusHistoryInline, DeliveryProofInline, DeliveryNotificationInline]

    fieldsets = [
        ('Delivery Info', {
            'fields': ['delivery_number', 'order', 'status']
        }),
        ('Assignment', {
            'fields': ['driver', 'zone', 'slot']
        }),
        ('Location', {
            'fields': ['address', 'latitude', 'longitude']
        }),
        ('Schedule', {
            'fields': ['scheduled_date', 'scheduled_time_start', 'scheduled_time_end']
        }),
        ('Notes', {
            'fields': ['notes', 'driver_notes', 'failure_reason'],
            'classes': ['collapse']
        }),
        ('Status Timestamps', {
            'fields': ['assigned_at', 'picked_up_at', 'out_for_delivery_at', 'arrived_at', 'delivered_at', 'failed_at'],
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def status_badge(self, obj):
        """Display colored status badge."""
        colors = {
            'pending': '#999',
            'assigned': '#17a2b8',
            'picked_up': '#ffc107',
            'out_for_delivery': '#fd7e14',
            'arrived': '#6f42c1',
            'delivered': '#28a745',
            'failed': '#dc3545',
            'returned': '#6c757d',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'


@admin.register(DeliveryStatusHistory)
class DeliveryStatusHistoryAdmin(admin.ModelAdmin):
    """Admin for delivery status history."""

    list_display = ['delivery', 'from_status', 'to_status', 'changed_by', 'created_at']
    list_filter = ['from_status', 'to_status']
    search_fields = ['delivery__delivery_number']
    raw_id_fields = ['delivery', 'changed_by']
    readonly_fields = ['delivery', 'from_status', 'to_status', 'changed_by', 'latitude', 'longitude', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DeliveryProof)
class DeliveryProofAdmin(admin.ModelAdmin):
    """Admin for delivery proofs."""

    list_display = ['delivery', 'proof_type', 'recipient_name', 'has_gps', 'created_at']
    list_filter = ['proof_type']
    search_fields = ['delivery__delivery_number', 'recipient_name']
    raw_id_fields = ['delivery']
    readonly_fields = ['created_at']

    def has_gps(self, obj):
        """Check if proof has GPS coordinates."""
        return bool(obj.latitude and obj.longitude)
    has_gps.boolean = True
    has_gps.short_description = 'Has GPS'


@admin.register(DeliveryRating)
class DeliveryRatingAdmin(admin.ModelAdmin):
    """Admin for delivery ratings."""

    list_display = ['delivery', 'rating', 'stars', 'comment_preview', 'created_at']
    list_filter = ['rating']
    search_fields = ['delivery__delivery_number', 'comment']
    raw_id_fields = ['delivery']
    readonly_fields = ['created_at']

    def stars(self, obj):
        """Display stars for rating."""
        return '⭐' * obj.rating
    stars.short_description = 'Rating'

    def comment_preview(self, obj):
        """Show truncated comment."""
        if obj.comment:
            return obj.comment[:50] + ('...' if len(obj.comment) > 50 else '')
        return '-'
    comment_preview.short_description = 'Comment'


@admin.register(DeliveryNotification)
class DeliveryNotificationAdmin(admin.ModelAdmin):
    """Admin for delivery notifications."""

    list_display = ['delivery', 'notification_type', 'recipient', 'status', 'sent_at', 'delivered_at']
    list_filter = ['notification_type', 'status']
    search_fields = ['delivery__delivery_number', 'recipient', 'message']
    raw_id_fields = ['delivery']
    readonly_fields = ['created_at']

    fieldsets = [
        ('Notification', {
            'fields': ['delivery', 'notification_type', 'recipient', 'message']
        }),
        ('Status', {
            'fields': ['status', 'external_id', 'sent_at', 'delivered_at', 'error_message']
        }),
        ('Audit', {
            'fields': ['created_at']
        }),
    ]

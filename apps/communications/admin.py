"""Admin configuration for omnichannel communications app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CommunicationChannel,
    MessageTemplate,
    Message,
    ReminderSchedule,
    EscalationRule,
)


@admin.register(CommunicationChannel)
class CommunicationChannelAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'channel_type', 'identifier',
        'is_verified', 'is_primary', 'created_at'
    ]
    list_filter = ['channel_type', 'is_verified', 'is_primary']
    search_fields = ['user__email', 'user__first_name', 'identifier']
    ordering = ['-created_at']
    raw_id_fields = ['user']

    fieldsets = (
        (None, {
            'fields': ('user', 'channel_type', 'identifier')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_primary')
        }),
        ('Preferences', {
            'fields': ('preferences',),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'channels_display', 'is_active', 'updated_at'
    ]
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject_es', 'subject_en', 'body_es', 'body_en']
    ordering = ['name']

    fieldsets = (
        (None, {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Spanish Content', {
            'fields': ('subject_es', 'body_es')
        }),
        ('English Content', {
            'fields': ('subject_en', 'body_en')
        }),
        ('Channels', {
            'fields': ('channels',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Channels')
    def channels_display(self, obj):
        if not obj.channels:
            return '-'
        return ', '.join(obj.channels)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'channel_badge', 'direction_badge', 'recipient',
        'status_badge', 'user', 'created_at'
    ]
    list_filter = ['channel', 'direction', 'status', 'created_at']
    search_fields = ['recipient', 'subject', 'body', 'user__email']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    raw_id_fields = ['user']

    fieldsets = (
        (None, {
            'fields': ('user', 'channel', 'direction')
        }),
        ('Message Details', {
            'fields': ('recipient', 'subject', 'body')
        }),
        ('Status', {
            'fields': ('status', 'external_id')
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'delivered_at', 'read_at', 'created_at'),
            'classes': ['collapse']
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ['collapse']
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Channel')
    def channel_badge(self, obj):
        colors = {
            'email': '#0d6efd',
            'sms': '#198754',
            'whatsapp': '#25D366',
            'voice': '#6f42c1',
        }
        color = colors.get(obj.channel, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.channel.upper()
        )

    @admin.display(description='Direction')
    def direction_badge(self, obj):
        if obj.direction == 'outbound':
            return format_html(
                '<span style="color: #0d6efd;">&#8594; OUT</span>'
            )
        return format_html(
            '<span style="color: #198754;">&#8592; IN</span>'
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'sent': '#0dcaf0',
            'delivered': '#198754',
            'read': '#0d6efd',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(ReminderSchedule)
class ReminderScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'reminder_type', 'scheduled_for', 'sent',
        'confirmed', 'created_at'
    ]
    list_filter = ['reminder_type', 'sent', 'confirmed', 'scheduled_for']
    search_fields = ['message']
    date_hierarchy = 'scheduled_for'
    ordering = ['scheduled_for']

    fieldsets = (
        (None, {
            'fields': ('reminder_type', 'scheduled_for', 'message')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Status', {
            'fields': ('sent', 'channels_attempted', 'confirmed', 'confirmed_at')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(EscalationRule)
class EscalationRuleAdmin(admin.ModelAdmin):
    list_display = [
        'reminder_type', 'step', 'channel', 'wait_hours', 'is_active'
    ]
    list_filter = ['reminder_type', 'channel', 'is_active']
    search_fields = ['reminder_type']
    ordering = ['reminder_type', 'step']

    fieldsets = (
        (None, {
            'fields': ('reminder_type', 'step', 'channel', 'wait_hours')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

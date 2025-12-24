"""Admin configuration for Email Marketing app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    NewsletterSubscription,
    EmailSegment,
    EmailTemplate,
    EmailCampaign,
    EmailSend,
    EmailLink,
    AutomatedSequence,
    SequenceStep,
    SequenceEnrollment,
)


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'status_badge', 'user', 'source',
        'confirmed_at', 'created_at'
    ]
    list_filter = ['status', 'source', 'created_at']
    search_fields = ['email', 'user__email']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'active': '#198754',
            'unsubscribed': '#6c757d',
            'bounced': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(EmailSegment)
class EmailSegmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'subscriber_count', 'is_dynamic', 'is_active', 'last_computed']
    list_filter = ['is_active', 'is_dynamic']
    search_fields = ['name', 'description']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'subject', 'is_active', 'updated_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject']


class EmailSendInline(admin.TabularInline):
    model = EmailSend
    extra = 0
    readonly_fields = ['subscription', 'status', 'sent_at', 'opened_at', 'clicked_at']
    can_delete = False


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'status_badge', 'segment', 'total_sent',
        'open_rate_display', 'click_rate_display', 'sent_at'
    ]
    list_filter = ['status', 'segment', 'sent_at']
    search_fields = ['name', 'subject']
    raw_id_fields = ['created_by', 'template', 'segment']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('name', 'template', 'segment', 'status')
        }),
        ('Content', {
            'fields': ('subject', 'subject_es', 'preview_text', 'html_content', 'text_content')
        }),
        ('Sender', {
            'fields': ('from_name', 'from_email', 'reply_to')
        }),
        ('Schedule', {
            'fields': ('scheduled_at', 'sent_at')
        }),
        ('A/B Testing', {
            'fields': ('ab_test_enabled', 'ab_test_subject_b'),
            'classes': ['collapse']
        }),
        ('Stats', {
            'fields': (
                'total_recipients', 'total_sent', 'total_delivered',
                'total_opened', 'total_clicked', 'total_bounced', 'total_unsubscribed'
            ),
            'classes': ['collapse']
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'scheduled': '#0d6efd',
            'sending': '#ffc107',
            'sent': '#198754',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description='Open Rate')
    def open_rate_display(self, obj):
        rate = obj.open_rate
        if rate >= 25:
            color = '#198754'
        elif rate >= 15:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )

    @admin.display(description='Click Rate')
    def click_rate_display(self, obj):
        rate = obj.click_rate
        if rate >= 5:
            color = '#198754'
        elif rate >= 2:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )


@admin.register(EmailSend)
class EmailSendAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'campaign', 'subscription', 'status_badge',
        'sent_at', 'opened_at', 'clicked_at'
    ]
    list_filter = ['status', 'campaign', 'sent_at']
    search_fields = ['subscription__email', 'campaign__name']
    raw_id_fields = ['campaign', 'subscription']
    date_hierarchy = 'sent_at'

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'queued': '#6c757d',
            'sent': '#0d6efd',
            'delivered': '#17a2b8',
            'opened': '#198754',
            'clicked': '#20c997',
            'bounced': '#dc3545',
            'complained': '#fd7e14',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(EmailLink)
class EmailLinkAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'original_url', 'click_count']
    list_filter = ['campaign']
    search_fields = ['original_url']


class SequenceStepInline(admin.TabularInline):
    model = SequenceStep
    extra = 0
    fields = ['step_number', 'template', 'delay_days', 'delay_hours', 'is_active']


@admin.register(AutomatedSequence)
class AutomatedSequenceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'trigger_type', 'step_count', 'total_enrolled',
        'total_completed', 'is_active'
    ]
    list_filter = ['trigger_type', 'is_active']
    search_fields = ['name', 'description']
    inlines = [SequenceStepInline]

    @admin.display(description='Steps')
    def step_count(self, obj):
        return obj.steps.count()


@admin.register(SequenceStep)
class SequenceStepAdmin(admin.ModelAdmin):
    list_display = ['sequence', 'step_number', 'template', 'delay_display', 'is_active']
    list_filter = ['sequence', 'is_active']
    raw_id_fields = ['sequence', 'template']

    @admin.display(description='Delay')
    def delay_display(self, obj):
        parts = []
        if obj.delay_days:
            parts.append(f"{obj.delay_days}d")
        if obj.delay_hours:
            parts.append(f"{obj.delay_hours}h")
        return ' '.join(parts) if parts else 'Immediate'


@admin.register(SequenceEnrollment)
class SequenceEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'subscription', 'sequence', 'status_badge', 'current_step',
        'enrolled_at', 'next_email_at'
    ]
    list_filter = ['status', 'sequence']
    search_fields = ['subscription__email']
    raw_id_fields = ['sequence', 'subscription']

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'active': '#198754',
            'completed': '#0d6efd',
            'paused': '#ffc107',
            'exited': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

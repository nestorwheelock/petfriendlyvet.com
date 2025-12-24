"""Admin configuration for Loyalty and Rewards app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    LoyaltyProgram,
    LoyaltyTier,
    LoyaltyAccount,
    PointTransaction,
    LoyaltyReward,
    RewardRedemption,
    ReferralProgram,
    Referral,
)


class LoyaltyTierInline(admin.TabularInline):
    model = LoyaltyTier
    extra = 0
    fields = ['name', 'min_points', 'max_points', 'discount_percent', 'points_multiplier', 'display_order']


@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_per_currency', 'tier_count', 'account_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    inlines = [LoyaltyTierInline]

    @admin.display(description='Tiers')
    def tier_count(self, obj):
        return obj.tiers.count()

    @admin.display(description='Accounts')
    def account_count(self, obj):
        return obj.accounts.count()


@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'program', 'min_points', 'max_points', 'discount_percent', 'points_multiplier']
    list_filter = ['program']
    ordering = ['program', 'display_order']


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'program', 'tier_badge', 'points_badge',
        'lifetime_points', 'is_active', 'enrolled_at'
    ]
    list_filter = ['program', 'tier', 'is_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    ordering = ['-lifetime_points']

    @admin.display(description='Tier')
    def tier_badge(self, obj):
        if not obj.tier:
            return '-'
        color = obj.tier.color or '#6c757d'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.tier.name
        )

    @admin.display(description='Balance')
    def points_badge(self, obj):
        return format_html(
            '<span style="font-weight: bold;">{:,}</span>',
            obj.points_balance
        )


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'account', 'type_badge', 'points_display',
        'balance_after', 'description', 'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['account__user__email', 'description']
    raw_id_fields = ['account', 'created_by']
    date_hierarchy = 'created_at'

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'earn': '#198754',
            'redeem': '#dc3545',
            'bonus': '#0d6efd',
            'adjustment': '#ffc107',
            'expire': '#6c757d',
            'referral': '#6f42c1',
        }
        color = colors.get(obj.transaction_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_transaction_type_display()
        )

    @admin.display(description='Points')
    def points_display(self, obj):
        if obj.points >= 0:
            return format_html(
                '<span style="color: #198754; font-weight: bold;">+{}</span>',
                obj.points
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">{}</span>',
            obj.points
        )


@admin.register(LoyaltyReward)
class LoyaltyRewardAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'program', 'reward_type', 'points_cost',
        'quantity_stats', 'is_active', 'is_featured'
    ]
    list_filter = ['program', 'reward_type', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    ordering = ['points_cost']

    fieldsets = (
        (None, {
            'fields': ('program', 'name', 'description', 'reward_type')
        }),
        ('Pricing', {
            'fields': ('points_cost', 'value', 'min_tier')
        }),
        ('Availability', {
            'fields': ('quantity_available', 'quantity_redeemed', 'valid_from', 'valid_until')
        }),
        ('Display', {
            'fields': ('is_active', 'is_featured')
        }),
    )

    @admin.display(description='Qty')
    def quantity_stats(self, obj):
        if obj.quantity_available:
            remaining = obj.quantity_available - obj.quantity_redeemed
            return f"{remaining}/{obj.quantity_available}"
        return f"{obj.quantity_redeemed} redeemed"


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'account', 'reward', 'points_spent',
        'status_badge', 'created_at', 'fulfilled_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['code', 'account__user__email', 'reward__name']
    raw_id_fields = ['account', 'reward', 'approved_by']
    date_hierarchy = 'created_at'

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'approved': '#0d6efd',
            'fulfilled': '#198754',
            'cancelled': '#dc3545',
            'expired': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@admin.register(ReferralProgram)
class ReferralProgramAdmin(admin.ModelAdmin):
    list_display = ['program', 'referrer_bonus', 'referred_bonus', 'is_active']
    list_filter = ['is_active']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'referrer', 'referred_email', 'referred',
        'status_badge', 'points_awarded', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['code', 'referrer__email', 'referred_email']
    raw_id_fields = ['referrer', 'referred']
    date_hierarchy = 'created_at'

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'completed': '#198754',
            'expired': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description='Points')
    def points_awarded(self, obj):
        total = obj.referrer_points_awarded + obj.referred_points_awarded
        if total > 0:
            return format_html(
                '<span style="color: #198754;">{}</span>',
                total
            )
        return '-'

"""Views for email marketing functionality."""
from django.db.models import Sum
from django.views.generic import TemplateView, ListView, DetailView

from apps.accounts.mixins import ModulePermissionMixin
from .models import (
    EmailCampaign, EmailTemplate, EmailSegment,
    NewsletterSubscription, AutomatedSequence
)


class MarketingPermissionMixin(ModulePermissionMixin):
    """Mixin requiring email_marketing module permission."""
    required_module = 'email_marketing'
    required_action = 'view'


class MarketingDashboardView(MarketingPermissionMixin, TemplateView):
    """Marketing dashboard with overview statistics."""

    template_name = 'email_marketing/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Subscriber stats
        context['total_subscribers'] = NewsletterSubscription.objects.count()
        context['active_subscribers'] = NewsletterSubscription.objects.filter(
            status='active'
        ).count()

        # Campaign stats
        context['total_campaigns'] = EmailCampaign.objects.count()
        context['sent_campaigns'] = EmailCampaign.objects.filter(
            status='sent'
        ).count()

        # Recent campaigns
        context['recent_campaigns'] = EmailCampaign.objects.select_related(
            'created_by', 'segment'
        ).order_by('-created_at')[:5]

        # Template count
        context['total_templates'] = EmailTemplate.objects.filter(
            is_active=True
        ).count()

        # Segment count
        context['total_segments'] = EmailSegment.objects.filter(
            is_active=True
        ).count()

        # Sequence count
        context['total_sequences'] = AutomatedSequence.objects.filter(
            is_active=True
        ).count()

        return context


class CampaignListView(MarketingPermissionMixin, ListView):
    """List of email campaigns."""

    model = EmailCampaign
    template_name = 'email_marketing/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 25

    def get_queryset(self):
        queryset = EmailCampaign.objects.select_related('created_by', 'segment')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')


class CampaignDetailView(MarketingPermissionMixin, DetailView):
    """Campaign detail with analytics."""

    model = EmailCampaign
    template_name = 'email_marketing/campaign_detail.html'
    context_object_name = 'campaign'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Recent sends
        context['recent_sends'] = self.object.sends.select_related(
            'subscription'
        ).order_by('-created_at')[:20]

        return context


class SubscriberListView(MarketingPermissionMixin, ListView):
    """List of newsletter subscribers."""

    model = NewsletterSubscription
    template_name = 'email_marketing/subscriber_list.html'
    context_object_name = 'subscribers'
    paginate_by = 50

    def get_queryset(self):
        queryset = NewsletterSubscription.objects.select_related('user')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')


class TemplateListView(MarketingPermissionMixin, ListView):
    """List of email templates."""

    model = EmailTemplate
    template_name = 'email_marketing/template_list.html'
    context_object_name = 'templates'
    paginate_by = 25

    def get_queryset(self):
        return EmailTemplate.objects.filter(is_active=True).order_by('name')


class SegmentListView(MarketingPermissionMixin, ListView):
    """List of email segments."""

    model = EmailSegment
    template_name = 'email_marketing/segment_list.html'
    context_object_name = 'segments'
    paginate_by = 25

    def get_queryset(self):
        return EmailSegment.objects.filter(is_active=True).order_by('name')


class SequenceListView(MarketingPermissionMixin, ListView):
    """List of automated sequences."""

    model = AutomatedSequence
    template_name = 'email_marketing/sequence_list.html'
    context_object_name = 'sequences'
    paginate_by = 25

    def get_queryset(self):
        return AutomatedSequence.objects.prefetch_related('steps').order_by('name')

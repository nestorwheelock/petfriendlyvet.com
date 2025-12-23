"""Views for external services."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView

from .models import ExternalPartner, Referral
from .forms import ReferralForm


class PartnerListView(LoginRequiredMixin, ListView):
    """List external service partners."""

    model = ExternalPartner
    template_name = 'services/partner_list.html'
    context_object_name = 'partners'

    def get_queryset(self):
        qs = ExternalPartner.objects.filter(is_active=True)

        # Filter by type if specified
        partner_type = self.request.GET.get('type')
        if partner_type:
            qs = qs.filter(partner_type=partner_type)

        return qs.order_by('-is_preferred', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partner_types'] = ExternalPartner.objects.filter(
            is_active=True
        ).values_list('partner_type', flat=True).distinct()
        context['selected_type'] = self.request.GET.get('type', '')
        return context


class PartnerDetailView(LoginRequiredMixin, DetailView):
    """View partner details."""

    model = ExternalPartner
    template_name = 'services/partner_detail.html'
    context_object_name = 'partner'

    def get_queryset(self):
        return ExternalPartner.objects.filter(is_active=True)


class ReferralCreateView(LoginRequiredMixin, CreateView):
    """Create a referral to a partner."""

    model = Referral
    form_class = ReferralForm
    template_name = 'services/referral_form.html'

    def get_partner(self):
        return get_object_or_404(
            ExternalPartner,
            pk=self.kwargs['partner_pk'],
            is_active=True
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partner'] = self.get_partner()
        return context

    def form_valid(self, form):
        partner = self.get_partner()
        form.instance.partner = partner
        form.instance.referred_by = self.request.user
        form.instance.service_type = partner.partner_type
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('services:referral_list')


class ReferralListView(LoginRequiredMixin, ListView):
    """List user's referrals."""

    model = Referral
    template_name = 'services/referral_list.html'
    context_object_name = 'referrals'

    def get_queryset(self):
        return Referral.objects.filter(
            pet__owner=self.request.user
        ).select_related('pet', 'partner').order_by('-created_at')

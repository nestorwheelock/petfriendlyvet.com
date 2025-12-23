"""Views for travel certificates."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView

from apps.pets.models import Pet
from .models import TravelDestination, HealthCertificate, TravelPlan
from .forms import CertificateRequestForm, TravelPlanForm


class DestinationListView(LoginRequiredMixin, ListView):
    """List travel destinations with requirements."""

    model = TravelDestination
    template_name = 'travel/destination_list.html'
    context_object_name = 'destinations'

    def get_queryset(self):
        return TravelDestination.objects.filter(is_active=True).order_by('country_name')


class DestinationDetailView(LoginRequiredMixin, DetailView):
    """View destination requirements."""

    model = TravelDestination
    template_name = 'travel/destination_detail.html'
    context_object_name = 'destination'

    def get_queryset(self):
        return TravelDestination.objects.filter(is_active=True)


class CertificateRequestView(LoginRequiredMixin, CreateView):
    """Request a health certificate for a pet."""

    model = HealthCertificate
    form_class = CertificateRequestForm
    template_name = 'travel/certificate_request.html'

    def get_pet(self):
        return get_object_or_404(
            Pet,
            pk=self.kwargs['pet_pk'],
            owner=self.request.user
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pet'] = self.get_pet()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pet'] = self.get_pet()
        return context

    def form_valid(self, form):
        form.instance.pet = self.get_pet()
        form.instance.issued_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('travel:certificate_list')


class CertificateListView(LoginRequiredMixin, ListView):
    """List user's health certificates."""

    model = HealthCertificate
    template_name = 'travel/certificate_list.html'
    context_object_name = 'certificates'

    def get_queryset(self):
        return HealthCertificate.objects.filter(
            pet__owner=self.request.user
        ).select_related('pet', 'destination').order_by('-created_at')


class CertificateDetailView(LoginRequiredMixin, DetailView):
    """View health certificate details."""

    model = HealthCertificate
    template_name = 'travel/certificate_detail.html'
    context_object_name = 'certificate'

    def get_queryset(self):
        return HealthCertificate.objects.filter(
            pet__owner=self.request.user
        ).select_related('pet', 'destination', 'issued_by')


class TravelPlanListView(LoginRequiredMixin, ListView):
    """List user's travel plans."""

    model = TravelPlan
    template_name = 'travel/travel_plan_list.html'
    context_object_name = 'travel_plans'

    def get_queryset(self):
        return TravelPlan.objects.filter(
            pet__owner=self.request.user
        ).select_related('pet', 'destination', 'certificate').order_by('-departure_date')


class TravelPlanCreateView(LoginRequiredMixin, CreateView):
    """Create a travel plan."""

    model = TravelPlan
    form_class = TravelPlanForm
    template_name = 'travel/travel_plan_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('travel:travel_plan_list')

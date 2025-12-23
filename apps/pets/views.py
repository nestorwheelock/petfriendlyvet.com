"""Views for pets management."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    TemplateView,
)

from .models import Pet, Vaccination, MedicalCondition
from .forms import PetForm


class OwnerDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard showing owner's pets and upcoming appointments."""

    template_name = 'pets/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's pets
        context['pets'] = Pet.objects.filter(owner=user).order_by('name')

        # Get upcoming appointments
        from apps.appointments.models import Appointment
        context['upcoming_appointments'] = Appointment.objects.filter(
            owner=user,
            scheduled_start__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).select_related('pet', 'service', 'veterinarian').order_by('scheduled_start')[:5]

        return context


class PetListView(LoginRequiredMixin, ListView):
    """List all pets belonging to the logged-in user."""

    model = Pet
    template_name = 'pets/pet_list.html'
    context_object_name = 'pets'

    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user).order_by('name')


class PetDetailView(LoginRequiredMixin, DetailView):
    """View details of a specific pet."""

    model = Pet
    template_name = 'pets/pet_detail.html'
    context_object_name = 'pet'

    def get_queryset(self):
        # Only allow access to user's own pets
        return Pet.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pet = self.object

        # Get vaccinations
        context['vaccinations'] = Vaccination.objects.filter(
            pet=pet
        ).order_by('-date_administered')

        # Get medical conditions
        context['medical_conditions'] = MedicalCondition.objects.filter(
            pet=pet
        ).order_by('-is_active', '-diagnosed_date')

        # Get recent appointments
        from apps.appointments.models import Appointment
        context['recent_appointments'] = Appointment.objects.filter(
            pet=pet
        ).select_related('service', 'veterinarian').order_by('-scheduled_start')[:5]

        return context


class PetCreateView(LoginRequiredMixin, CreateView):
    """Create a new pet."""

    model = Pet
    form_class = PetForm
    template_name = 'pets/pet_form.html'
    success_url = reverse_lazy('pets:pet_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class PetUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing pet."""

    model = Pet
    form_class = PetForm
    template_name = 'pets/pet_form.html'

    def get_queryset(self):
        # Only allow editing user's own pets
        return Pet.objects.filter(owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy('pets:pet_detail', kwargs={'pk': self.object.pk})

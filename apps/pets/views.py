"""Views for pets management."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
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

        # Get user's active (non-archived) pets
        context['pets'] = Pet.objects.filter(owner=user, is_archived=False).order_by('name')

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
        show_archived = self.request.GET.get('archived') == '1'
        qs = Pet.objects.filter(owner=self.request.user)
        if not show_archived:
            qs = qs.filter(is_archived=False)
        return qs.order_by('is_archived', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_archived'] = self.request.GET.get('archived') == '1'
        context['archived_count'] = Pet.objects.filter(
            owner=self.request.user, is_archived=True
        ).count()
        return context


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


class PetArchiveView(LoginRequiredMixin, View):
    """Archive a pet (soft delete)."""

    def post(self, request, pk):
        pet = get_object_or_404(Pet, pk=pk, owner=request.user)
        pet.is_archived = True
        pet.save(update_fields=['is_archived', 'updated_at'])
        messages.success(request, _('%(name)s has been archived.') % {'name': pet.name})
        return redirect('pets:pet_list')


class PetUnarchiveView(LoginRequiredMixin, View):
    """Restore an archived pet."""

    def post(self, request, pk):
        pet = get_object_or_404(Pet, pk=pk, owner=request.user, is_archived=True)
        pet.is_archived = False
        pet.save(update_fields=['is_archived', 'updated_at'])
        messages.success(request, _('%(name)s has been restored.') % {'name': pet.name})
        return redirect('pets:pet_detail', pk=pet.pk)


class PetMarkDeceasedView(LoginRequiredMixin, View):
    """Mark a pet as deceased with date."""

    def post(self, request, pk):
        from datetime import datetime
        pet = get_object_or_404(Pet, pk=pk, owner=request.user)

        # Parse date from form or use today
        date_str = request.POST.get('deceased_date')
        if date_str:
            try:
                deceased_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                deceased_date = timezone.now().date()
        else:
            deceased_date = timezone.now().date()

        pet.deceased_date = deceased_date
        pet.is_archived = True
        pet.save(update_fields=['deceased_date', 'is_archived', 'updated_at'])
        messages.info(request, _('We\'re sorry for your loss. %(name)s\'s profile has been preserved in your archived pets.') % {'name': pet.name})
        return redirect('pets:pet_list')

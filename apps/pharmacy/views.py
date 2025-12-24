"""Views for pharmacy functionality."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.http import Http404

from .models import Prescription, RefillRequest


class PrescriptionListView(LoginRequiredMixin, ListView):
    """List all prescriptions for the logged-in user."""

    model = Prescription
    template_name = 'pharmacy/prescription_list.html'
    context_object_name = 'prescriptions'

    def get_queryset(self):
        return Prescription.objects.filter(
            owner=self.request.user
        ).select_related('pet', 'medication', 'prescribing_vet__user').order_by('-prescribed_date')


class PrescriptionDetailView(LoginRequiredMixin, DetailView):
    """View details of a specific prescription."""

    model = Prescription
    template_name = 'pharmacy/prescription_detail.html'
    context_object_name = 'prescription'

    def get_queryset(self):
        return Prescription.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prescription = self.object

        context['fills'] = prescription.fills.all().order_by('-requested_at')
        context['refill_requests'] = prescription.refill_requests.all().order_by('-created_at')
        context['can_refill'] = prescription.can_refill

        return context


class RefillRequestCreateView(LoginRequiredMixin, CreateView):
    """Create a refill request for a prescription."""

    model = RefillRequest
    fields = ['notes']
    template_name = 'pharmacy/refill_request_form.html'

    def get_prescription(self):
        prescription = get_object_or_404(
            Prescription,
            pk=self.kwargs['prescription_id'],
            owner=self.request.user
        )
        return prescription

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prescription'] = self.get_prescription()
        return context

    def form_valid(self, form):
        prescription = self.get_prescription()

        if not prescription.can_refill:
            messages.error(self.request, 'This prescription cannot be refilled.')
            return redirect('pharmacy:prescription_detail', pk=prescription.pk)

        if prescription.medication.is_controlled:
            messages.error(
                self.request,
                'Controlled substances cannot be refilled online. Please call the clinic.'
            )
            return redirect('pharmacy:prescription_detail', pk=prescription.pk)

        form.instance.prescription = prescription
        form.instance.requested_by = self.request.user

        messages.success(self.request, 'Refill request submitted successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('pharmacy:refill_list')


class RefillListView(LoginRequiredMixin, ListView):
    """List all refill requests for the logged-in user."""

    model = RefillRequest
    template_name = 'pharmacy/refill_list.html'
    context_object_name = 'refill_requests'

    def get_queryset(self):
        return RefillRequest.objects.filter(
            requested_by=self.request.user
        ).select_related(
            'prescription__medication',
            'prescription__pet'
        ).order_by('-created_at')


class RefillDetailView(LoginRequiredMixin, DetailView):
    """View details of a specific refill request."""

    model = RefillRequest
    template_name = 'pharmacy/refill_detail.html'
    context_object_name = 'refill_request'

    def get_queryset(self):
        return RefillRequest.objects.filter(requested_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        refill = self.object

        context['prescription'] = refill.prescription
        if refill.fill:
            context['fill'] = refill.fill

        return context

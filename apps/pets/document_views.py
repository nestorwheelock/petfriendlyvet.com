"""Views for pet document management."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, DeleteView

from .models import Pet, PetDocument
from .forms import PetDocumentForm


class DocumentListView(LoginRequiredMixin, ListView):
    """List documents for a pet."""

    model = PetDocument
    template_name = 'pets/document_list.html'
    context_object_name = 'documents'

    def get_pet(self):
        """Get the pet, checking access permissions."""
        user = self.request.user
        pet_pk = self.kwargs['pet_pk']

        # Staff can see any pet's documents
        if user.role in ['staff', 'vet', 'admin']:
            return get_object_or_404(Pet, pk=pet_pk)

        # Owners can only see their own pets
        return get_object_or_404(Pet, pk=pet_pk, owner=user)

    def get_queryset(self):
        pet = self.get_pet()
        user = self.request.user

        qs = PetDocument.objects.filter(pet=pet)

        # Filter by visibility for non-staff
        if user.role not in ['staff', 'vet', 'admin']:
            qs = qs.filter(visible_to_owner=True)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pet'] = self.get_pet()
        return context


class DocumentUploadView(LoginRequiredMixin, CreateView):
    """Upload a document for a pet."""

    model = PetDocument
    form_class = PetDocumentForm
    template_name = 'pets/document_form.html'

    def get_pet(self):
        """Get the pet, checking ownership."""
        user = self.request.user
        pet_pk = self.kwargs['pet_pk']

        # Staff can upload to any pet
        if user.role in ['staff', 'vet', 'admin']:
            return get_object_or_404(Pet, pk=pet_pk)

        # Owners can only upload to their own pets
        return get_object_or_404(Pet, pk=pet_pk, owner=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pet'] = self.get_pet()
        return context

    def form_valid(self, form):
        pet = self.get_pet()
        form.instance.pet = pet
        form.instance.uploaded_by = self.request.user

        # Only staff can set visibility
        if self.request.user.role not in ['staff', 'vet', 'admin']:
            form.instance.visible_to_owner = True

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('pets:document_list', kwargs={'pet_pk': self.kwargs['pet_pk']})


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a pet document."""

    model = PetDocument
    template_name = 'pets/document_confirm_delete.html'

    def get_queryset(self):
        user = self.request.user
        pet_pk = self.kwargs['pet_pk']

        # Staff can delete any document
        if user.role in ['staff', 'vet', 'admin']:
            return PetDocument.objects.filter(pet_id=pet_pk)

        # Owners can only delete from their own pets
        return PetDocument.objects.filter(
            pet_id=pet_pk,
            pet__owner=user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pet'] = self.object.pet
        return context

    def get_success_url(self):
        return reverse('pets:document_list', kwargs={'pet_pk': self.kwargs['pet_pk']})

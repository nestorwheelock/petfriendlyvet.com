"""Views for the Parties module - People, Organizations, Groups, Relationships."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, TemplateView,
    CreateView, UpdateView, DeleteView
)

from .models import Person, Organization, Group, PartyRelationship, Demographics
from .forms import PersonForm, OrganizationForm, GroupForm, PartyRelationshipForm, DemographicsForm


class StaffRequiredMixin(LoginRequiredMixin):
    """Require staff or superuser access."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_staff or request.user.is_superuser):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class PartiesDashboardView(StaffRequiredMixin, TemplateView):
    """Dashboard for parties module."""

    template_name = 'parties/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['people_count'] = Person.objects.count()
        context['organizations_count'] = Organization.objects.count()
        context['groups_count'] = Group.objects.count()
        context['relationships_count'] = PartyRelationship.objects.count()
        return context


class PeopleListView(StaffRequiredMixin, ListView):
    """List all people."""

    model = Person
    template_name = 'parties/people_list.html'
    context_object_name = 'people'
    paginate_by = 25

    def get_queryset(self):
        return Person.objects.prefetch_related('accounts').order_by('last_name', 'first_name')


class PersonDetailView(StaffRequiredMixin, DetailView):
    """Detail view for a person."""

    model = Person
    template_name = 'parties/person_detail.html'
    context_object_name = 'person'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.object
        context['relationships'] = person.relationships_from.select_related(
            'to_person', 'to_organization', 'to_group'
        )
        context['accounts'] = person.accounts.all()
        context['addresses'] = person.addresses.all()
        context['phone_numbers'] = person.phone_numbers.all()
        context['email_addresses'] = person.email_addresses.all()
        context['owned_pets'] = person.owned_pets.all()
        context['pet_responsibilities'] = person.pet_responsibilities.select_related('pet')
        return context


class OrganizationsListView(StaffRequiredMixin, ListView):
    """List all organizations."""

    model = Organization
    template_name = 'parties/organizations_list.html'
    context_object_name = 'organizations'
    paginate_by = 25

    def get_queryset(self):
        return Organization.objects.order_by('name')


class OrganizationDetailView(StaffRequiredMixin, DetailView):
    """Detail view for an organization."""

    model = Organization
    template_name = 'parties/organization_detail.html'
    context_object_name = 'organization'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.object
        context['members'] = org.relationships_to.select_related('from_person')
        return context


class GroupsListView(StaffRequiredMixin, ListView):
    """List all groups (households, families)."""

    model = Group
    template_name = 'parties/groups_list.html'
    context_object_name = 'groups'
    paginate_by = 25

    def get_queryset(self):
        return Group.objects.select_related('primary_contact').order_by('name')


class GroupDetailView(StaffRequiredMixin, DetailView):
    """Detail view for a group."""

    model = Group
    template_name = 'parties/group_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        context['members'] = group.relationships_to.select_related('from_person')
        return context


class RelationshipsListView(StaffRequiredMixin, ListView):
    """List all party relationships."""

    model = PartyRelationship
    template_name = 'parties/relationships_list.html'
    context_object_name = 'relationships'
    paginate_by = 25

    def get_queryset(self):
        return PartyRelationship.objects.select_related(
            'from_person', 'from_organization',
            'to_person', 'to_organization', 'to_group'
        ).order_by('-created_at')


# =============================================================================
# Person CRUD Views
# =============================================================================

class PersonCreateView(StaffRequiredMixin, CreateView):
    """Create a new person."""

    model = Person
    form_class = PersonForm
    template_name = 'parties/person_form.html'
    success_url = reverse_lazy('parties:people_list')

    def form_valid(self, form):
        messages.success(self.request, f"Person '{form.instance.first_name}' created successfully.")
        return super().form_valid(form)


class PersonUpdateView(StaffRequiredMixin, UpdateView):
    """Edit an existing person."""

    model = Person
    form_class = PersonForm
    template_name = 'parties/person_form.html'
    context_object_name = 'person'

    def get_success_url(self):
        return reverse_lazy('parties:person_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Person '{form.instance.first_name}' updated successfully.")
        return super().form_valid(form)


class PersonDeleteView(StaffRequiredMixin, DeleteView):
    """Delete a person."""

    model = Person
    template_name = 'parties/person_confirm_delete.html'
    success_url = reverse_lazy('parties:people_list')
    context_object_name = 'person'

    def form_valid(self, form):
        messages.success(self.request, f"Person '{self.object}' deleted successfully.")
        return super().form_valid(form)


# =============================================================================
# Organization CRUD Views
# =============================================================================

class OrganizationCreateView(StaffRequiredMixin, CreateView):
    """Create a new organization."""

    model = Organization
    form_class = OrganizationForm
    template_name = 'parties/organization_form.html'
    success_url = reverse_lazy('parties:organizations_list')

    def form_valid(self, form):
        messages.success(self.request, f"Organization '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class OrganizationUpdateView(StaffRequiredMixin, UpdateView):
    """Edit an existing organization."""

    model = Organization
    form_class = OrganizationForm
    template_name = 'parties/organization_form.html'
    context_object_name = 'organization'

    def get_success_url(self):
        return reverse_lazy('parties:organization_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Organization '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class OrganizationDeleteView(StaffRequiredMixin, DeleteView):
    """Delete an organization."""

    model = Organization
    template_name = 'parties/organization_confirm_delete.html'
    success_url = reverse_lazy('parties:organizations_list')
    context_object_name = 'organization'

    def form_valid(self, form):
        messages.success(self.request, f"Organization '{self.object}' deleted successfully.")
        return super().form_valid(form)


# =============================================================================
# Group CRUD Views
# =============================================================================

class GroupCreateView(StaffRequiredMixin, CreateView):
    """Create a new group (household/family)."""

    model = Group
    form_class = GroupForm
    template_name = 'parties/group_form.html'
    success_url = reverse_lazy('parties:groups_list')

    def form_valid(self, form):
        messages.success(self.request, f"Group '{form.instance.name}' created successfully.")
        return super().form_valid(form)


class GroupUpdateView(StaffRequiredMixin, UpdateView):
    """Edit an existing group."""

    model = Group
    form_class = GroupForm
    template_name = 'parties/group_form.html'
    context_object_name = 'group'

    def get_success_url(self):
        return reverse_lazy('parties:group_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Group '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class GroupDeleteView(StaffRequiredMixin, DeleteView):
    """Delete a group."""

    model = Group
    template_name = 'parties/group_confirm_delete.html'
    success_url = reverse_lazy('parties:groups_list')
    context_object_name = 'group'

    def form_valid(self, form):
        messages.success(self.request, f"Group '{self.object}' deleted successfully.")
        return super().form_valid(form)


# =============================================================================
# Relationship CRUD Views
# =============================================================================

class RelationshipCreateView(StaffRequiredMixin, CreateView):
    """Create a new party relationship."""

    model = PartyRelationship
    form_class = PartyRelationshipForm
    template_name = 'parties/relationship_form.html'
    success_url = reverse_lazy('parties:relationships_list')

    def form_valid(self, form):
        messages.success(self.request, "Relationship created successfully.")
        return super().form_valid(form)


class RelationshipUpdateView(StaffRequiredMixin, UpdateView):
    """Edit an existing relationship."""

    model = PartyRelationship
    form_class = PartyRelationshipForm
    template_name = 'parties/relationship_form.html'
    success_url = reverse_lazy('parties:relationships_list')
    context_object_name = 'relationship'

    def form_valid(self, form):
        messages.success(self.request, "Relationship updated successfully.")
        return super().form_valid(form)


class RelationshipDeleteView(StaffRequiredMixin, DeleteView):
    """Delete a relationship."""

    model = PartyRelationship
    template_name = 'parties/relationship_confirm_delete.html'
    success_url = reverse_lazy('parties:relationships_list')
    context_object_name = 'relationship'

    def form_valid(self, form):
        messages.success(self.request, "Relationship deleted successfully.")
        return super().form_valid(form)


# =============================================================================
# Person Pet Management Views
# =============================================================================

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from django.views import View
from apps.pets.models import Pet, SPECIES_CHOICES


class PersonAddPetView(StaffRequiredMixin, TemplateView):
    """Add a pet to a person - search existing or create new."""

    template_name = 'parties/person_add_pet.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = get_object_or_404(Person, pk=self.kwargs['pk'])
        context['species_choices'] = SPECIES_CHOICES
        return context

    def post(self, request, pk):
        person = get_object_or_404(Person, pk=pk)
        action = request.POST.get('action')

        if action == 'link_existing':
            # Link an existing pet to this person
            pet_id = request.POST.get('pet_id')
            pet = get_object_or_404(Pet, pk=pet_id)
            pet.owner_person = person
            pet.save(update_fields=['owner_person'])
            messages.success(request, f"Pet '{pet.name}' linked to {person.get_full_name()}.")

        elif action == 'create_new':
            # Create a new pet for this person
            pet = Pet.objects.create(
                name=request.POST.get('name'),
                species=request.POST.get('species'),
                breed=request.POST.get('breed', ''),
                owner_person=person,
            )
            messages.success(request, f"Pet '{pet.name}' created for {person.get_full_name()}.")

        return redirect('parties:person_detail', pk=pk)


class PersonSearchPetsView(StaffRequiredMixin, View):
    """AJAX endpoint to search for pets."""

    def get(self, request, pk):
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'pets': []})

        pets = Pet.objects.filter(
            Q(name__icontains=query) |
            Q(breed__icontains=query)
        ).select_related('owner_person')[:20]

        current_person_pk = int(pk)
        results = []
        for pet in pets:
            owner_name = pet.owner_person.get_full_name() if pet.owner_person else None
            owner_pk = pet.owner_person.pk if pet.owner_person else None
            results.append({
                'id': pet.pk,
                'name': pet.name,
                'species': pet.get_species_display(),
                'breed': pet.breed or '',
                'owner': owner_name,
                'owner_pk': owner_pk,
                'has_different_owner': owner_pk is not None and owner_pk != current_person_pk,
            })

        return JsonResponse({'pets': results})


class PersonUnlinkPetView(StaffRequiredMixin, View):
    """Remove a pet from a person (unlink ownership)."""

    def post(self, request, pk, pet_pk):
        person = get_object_or_404(Person, pk=pk)
        pet = get_object_or_404(Pet, pk=pet_pk, owner_person=person)

        pet.owner_person = None
        pet.save(update_fields=['owner_person'])

        messages.success(request, f"Pet '{pet.name}' unlinked from {person.get_full_name()}.")
        return redirect('parties:person_detail', pk=pk)

"""Views for CRM functionality."""
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView, ListView, DetailView

from apps.accounts.decorators import require_permission
from apps.accounts.mixins import ModulePermissionMixin
from apps.accounts.models import User
from .models import OwnerProfile, CustomerTag, Interaction


class CRMPermissionMixin(ModulePermissionMixin):
    """Mixin requiring CRM module permission."""
    required_module = 'crm'
    required_action = 'view'


class CRMDashboardView(CRMPermissionMixin, TemplateView):
    """CRM dashboard for customer management."""

    template_name = 'crm/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Customer stats
        context['total_customers'] = OwnerProfile.objects.count()
        context['new_customers_month'] = OwnerProfile.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()

        # Recent interactions
        context['recent_interactions'] = Interaction.objects.select_related(
            'owner_profile__user', 'handled_by'
        ).order_by('-created_at')[:10]

        # Follow-ups due
        context['followups_due'] = Interaction.objects.filter(
            follow_up_required=True,
            follow_up_date__lte=timezone.now().date()
        ).select_related('owner_profile__user').order_by('follow_up_date')[:5]

        # Customer tags with counts
        context['tags'] = CustomerTag.objects.filter(is_active=True).annotate(
            customer_count=Count('profiles')
        ).order_by('-customer_count')[:10]

        # Top customers by spend
        context['top_customers'] = OwnerProfile.objects.filter(
            total_spent__gt=0
        ).select_related('user').order_by('-total_spent')[:5]

        return context


class CustomerListView(CRMPermissionMixin, ListView):
    """List all customers."""

    model = OwnerProfile
    template_name = 'crm/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 25

    def get_queryset(self):
        return OwnerProfile.objects.select_related('user').order_by('-created_at')


class CustomerDetailView(CRMPermissionMixin, DetailView):
    """View customer details."""

    model = OwnerProfile
    template_name = 'crm/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object

        # Get interactions
        context['interactions'] = customer.interactions.select_related(
            'handled_by'
        ).order_by('-created_at')[:20]

        # Get notes
        context['notes'] = customer.customer_notes.select_related(
            'author'
        ).order_by('-is_pinned', '-created_at')[:10]

        # Get pets
        context['pets'] = customer.user.pets.all()

        return context


@login_required
@require_permission('crm', 'view')
def customer_by_user(request, user_id):
    """Redirect to customer detail by user ID.

    This is used from encounter cards where we have user.id (pet owner)
    but need to display the OwnerProfile CRM page.
    """
    user = get_object_or_404(User, pk=user_id)

    # Get or create OwnerProfile for this user
    profile, created = OwnerProfile.objects.get_or_create(user=user)

    # Get staff token for redirect
    staff_token = request.session.get('staff_token', '')

    # Redirect to the profile detail page
    return redirect(f'/staff-{staff_token}/customers/crm/customers/{profile.pk}/')

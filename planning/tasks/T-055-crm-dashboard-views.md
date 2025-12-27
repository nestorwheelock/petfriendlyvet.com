# T-055: CRM Dashboard & Views

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement CRM dashboard and owner management interface
**Related Story**: S-007
**Epoch**: 5
**Estimate**: 5 hours

### Constraints
**Allowed File Paths**: apps/crm/, templates/admin/crm/
**Forbidden Paths**: None

### Deliverables
- [ ] CRM dashboard with KPIs
- [ ] Owner list with filters
- [ ] Owner detail view
- [ ] Interaction logging
- [ ] Segment management
- [ ] Follow-up tracking

### Wireframe Reference
See: `planning/wireframes/19-crm-dashboard.txt`

### Implementation Details

#### Views
```python
class CRMDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """CRM dashboard with key metrics."""

    template_name = 'admin/crm/dashboard.html'
    permission_required = 'crm.view_ownerprofile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Key metrics
        profiles = OwnerProfile.objects.all()

        context['total_customers'] = profiles.count()
        context['active_customers'] = profiles.filter(
            days_since_last_visit__lte=90
        ).count()
        context['at_risk'] = profiles.filter(churn_risk='high').count()
        context['new_this_month'] = profiles.filter(
            created_at__month=timezone.now().month
        ).count()

        # Revenue metrics
        context['total_ltv'] = profiles.aggregate(
            total=Sum('lifetime_value')
        )['total'] or 0
        context['avg_ltv'] = profiles.aggregate(
            avg=Avg('lifetime_value')
        )['avg'] or 0

        # Tier distribution
        context['tier_distribution'] = profiles.values('tier').annotate(
            count=Count('id')
        ).order_by('tier')

        # Churn risk distribution
        context['risk_distribution'] = profiles.values('churn_risk').annotate(
            count=Count('id')
        )

        # Recent interactions
        context['recent_interactions'] = OwnerInteraction.objects.select_related(
            'owner', 'pet'
        ).order_by('-created_at')[:10]

        # Pending follow-ups
        context['pending_followups'] = OwnerInteraction.objects.filter(
            requires_follow_up=True,
            follow_up_completed=False,
            follow_up_date__lte=timezone.now().date()
        ).select_related('owner')[:10]

        # Segments
        context['segments'] = CustomerSegment.objects.filter(
            is_active=True
        ).order_by('-member_count')[:5]

        return context


class OwnerListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List of owners with CRM data."""

    model = OwnerProfile
    template_name = 'admin/crm/owner_list.html'
    context_object_name = 'owners'
    permission_required = 'crm.view_ownerprofile'
    paginate_by = 25

    def get_queryset(self):
        queryset = OwnerProfile.objects.select_related('owner')

        # Tier filter
        tier = self.request.GET.get('tier')
        if tier:
            queryset = queryset.filter(tier=tier)

        # Risk filter
        risk = self.request.GET.get('risk')
        if risk:
            queryset = queryset.filter(churn_risk=risk)

        # Tag filter
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])

        # Segment filter
        segment_id = self.request.GET.get('segment')
        if segment_id:
            segment = CustomerSegment.objects.get(id=segment_id)
            queryset = segment.get_members()

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(owner__first_name__icontains=search) |
                Q(owner__last_name__icontains=search) |
                Q(owner__email__icontains=search) |
                Q(phone__icontains=search)
            )

        # Sort
        sort = self.request.GET.get('sort', '-last_visit_date')
        queryset = queryset.order_by(sort)

        return queryset


class OwnerDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detailed owner profile with full history."""

    model = OwnerProfile
    template_name = 'admin/crm/owner_detail.html'
    context_object_name = 'profile'
    permission_required = 'crm.view_ownerprofile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner = self.object.owner

        # Pets
        context['pets'] = owner.pets.all()

        # Appointments
        context['appointments'] = owner.appointments.order_by('-start_time')[:10]

        # Orders
        context['orders'] = owner.orders.order_by('-created_at')[:10]

        # Interactions
        context['interactions'] = owner.interactions.order_by('-created_at')[:20]

        # Conversations
        context['conversations'] = owner.conversations.order_by('-last_message_at')[:5]

        # Timeline (combined activity)
        context['timeline'] = self._build_timeline(owner)

        return context

    def _build_timeline(self, owner):
        """Build activity timeline."""
        from itertools import chain
        from operator import attrgetter

        appointments = list(owner.appointments.all()[:20])
        orders = list(owner.orders.all()[:20])
        interactions = list(owner.interactions.all()[:20])

        # Add type attribute for template
        for apt in appointments:
            apt.timeline_type = 'appointment'
            apt.timeline_date = apt.start_time
        for order in orders:
            order.timeline_type = 'order'
            order.timeline_date = order.created_at
        for interaction in interactions:
            interaction.timeline_type = 'interaction'
            interaction.timeline_date = interaction.created_at

        combined = list(chain(appointments, orders, interactions))
        return sorted(combined, key=attrgetter('timeline_date'), reverse=True)[:30]


class LogInteractionView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Log new interaction with owner."""

    model = OwnerInteraction
    template_name = 'admin/crm/log_interaction.html'
    permission_required = 'crm.add_ownerinteraction'
    fields = [
        'interaction_type', 'direction', 'subject', 'summary',
        'outcome', 'pet', 'sentiment', 'requires_follow_up', 'follow_up_date'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['owner'] = get_object_or_404(User, pk=self.kwargs['owner_pk'])
        context['pets'] = context['owner'].pets.all()
        return context

    def form_valid(self, form):
        form.instance.owner_id = self.kwargs['owner_pk']
        form.instance.handled_by = self.request.user
        return super().form_valid(form)


class FollowUpListView(LoginRequiredMixin, ListView):
    """List of pending follow-ups."""

    model = OwnerInteraction
    template_name = 'admin/crm/followups.html'
    context_object_name = 'followups'

    def get_queryset(self):
        return OwnerInteraction.objects.filter(
            requires_follow_up=True,
            follow_up_completed=False
        ).select_related('owner', 'pet').order_by('follow_up_date')
```

#### Dashboard Template (snippet)
```html
<!-- templates/admin/crm/dashboard.html -->
{% extends "admin/base.html" %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold mb-6">{% trans 'CRM Dashboard' %}</h1>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-gray-600 text-sm">{% trans 'Total Clientes' %}</p>
            <p class="text-3xl font-bold">{{ total_customers }}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-gray-600 text-sm">{% trans 'Clientes Activos' %}</p>
            <p class="text-3xl font-bold text-green-600">{{ active_customers }}</p>
            <p class="text-xs text-gray-500">{% trans 'Última visita < 90 días' %}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-gray-600 text-sm">{% trans 'En Riesgo' %}</p>
            <p class="text-3xl font-bold text-red-600">{{ at_risk }}</p>
            <p class="text-xs text-gray-500">{% trans 'Sin visita > 180 días' %}</p>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
            <p class="text-gray-600 text-sm">{% trans 'LTV Promedio' %}</p>
            <p class="text-3xl font-bold">${{ avg_ltv|floatformat:0 }}</p>
        </div>
    </div>

    <!-- Two columns -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Pending Follow-ups -->
        <div class="bg-white rounded-lg shadow">
            <div class="p-4 border-b">
                <h2 class="font-semibold">{% trans 'Seguimientos Pendientes' %}</h2>
            </div>
            <div class="p-4">
                {% for followup in pending_followups %}
                <div class="flex justify-between items-center py-2 border-b last:border-0">
                    <div>
                        <p class="font-medium">{{ followup.owner.get_full_name }}</p>
                        <p class="text-sm text-gray-600">{{ followup.subject|truncatechars:50 }}</p>
                    </div>
                    <span class="text-sm {% if followup.follow_up_date < today %}text-red-600{% else %}text-gray-500{% endif %}">
                        {{ followup.follow_up_date|date:"d M" }}
                    </span>
                </div>
                {% empty %}
                <p class="text-gray-500">{% trans 'No hay seguimientos pendientes' %}</p>
                {% endfor %}
            </div>
        </div>

        <!-- Recent Interactions -->
        <div class="bg-white rounded-lg shadow">
            <div class="p-4 border-b">
                <h2 class="font-semibold">{% trans 'Interacciones Recientes' %}</h2>
            </div>
            <div class="p-4">
                {% for interaction in recent_interactions %}
                <div class="flex items-start gap-3 py-2 border-b last:border-0">
                    <span class="text-xl">
                        {% if interaction.interaction_type == 'visit' %}🏥
                        {% elif interaction.interaction_type == 'call_in' %}📞
                        {% elif interaction.interaction_type == 'whatsapp' %}💬
                        {% else %}📝{% endif %}
                    </span>
                    <div class="flex-grow">
                        <p class="font-medium">{{ interaction.owner.get_full_name }}</p>
                        <p class="text-sm text-gray-600">{{ interaction.summary|truncatechars:50 }}</p>
                    </div>
                    <span class="text-xs text-gray-500">{{ interaction.created_at|timesince }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Test Cases
- [ ] Dashboard KPIs accurate
- [ ] Owner list with filters
- [ ] Owner detail shows history
- [ ] Timeline combines correctly
- [ ] Interaction logging works
- [ ] Follow-up list shows pending
- [ ] Segment filtering works

### Definition of Done
- [ ] All views implemented
- [ ] Dashboard is responsive
- [ ] Real-time updates via HTMX
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-054: CRM Owner Models
- T-002: Base Templates

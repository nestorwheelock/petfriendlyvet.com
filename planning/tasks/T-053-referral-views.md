# T-053: Referral Network Views & Admin

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement referral management interface
**Related Story**: S-025
**Epoch**: 4
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/vet_clinic/, templates/admin/referrals/
**Forbidden Paths**: None

### Deliverables
- [ ] Specialist directory view
- [ ] Referral creation form
- [ ] Referral tracking dashboard
- [ ] Visiting schedule calendar
- [ ] Document management

### Implementation Details

#### Views
```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class SpecialistDirectoryView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Directory of specialists and partners."""

    model = Specialist
    template_name = 'admin/referrals/directory.html'
    context_object_name = 'specialists'
    permission_required = 'vet_clinic.view_specialist'

    def get_queryset(self):
        queryset = Specialist.objects.filter(is_active=True)

        # Filter by type
        partner_type = self.request.GET.get('type')
        if partner_type:
            queryset = queryset.filter(partner_type=partner_type)

        # Filter by specialty
        specialty = self.request.GET.get('specialty')
        if specialty:
            queryset = queryset.filter(specialties__slug=specialty)

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(city__icontains=search) |
                Q(services__icontains=search)
            )

        return queryset.prefetch_related('specialties')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specialties'] = Specialty.objects.filter(is_active=True)
        context['partner_types'] = Specialist.PARTNER_TYPES
        return context


class SpecialistDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Specialist detail page."""

    model = Specialist
    template_name = 'admin/referrals/specialist_detail.html'
    permission_required = 'vet_clinic.view_specialist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Recent referrals
        context['recent_referrals'] = Referral.objects.filter(
            specialist=self.object
        ).order_by('-referred_date')[:10]

        # Upcoming visits if visiting specialist
        if self.object.is_visiting:
            context['upcoming_visits'] = VisitingSchedule.objects.filter(
                specialist=self.object,
                date__gte=timezone.now().date()
            ).order_by('date')[:5]

        # Stats
        context['referral_count'] = Referral.objects.filter(
            specialist=self.object
        ).count()

        return context


class ReferralListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List of referrals."""

    model = Referral
    template_name = 'admin/referrals/referral_list.html'
    context_object_name = 'referrals'
    permission_required = 'vet_clinic.view_referral'
    paginate_by = 20

    def get_queryset(self):
        queryset = Referral.objects.select_related(
            'pet', 'owner', 'specialist'
        )

        # Direction filter
        direction = self.request.GET.get('direction')
        if direction:
            queryset = queryset.filter(direction=direction)

        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Date range
        date_from = self.request.GET.get('from')
        date_to = self.request.GET.get('to')
        if date_from:
            queryset = queryset.filter(referred_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(referred_date__lte=date_to)

        return queryset.order_by('-referred_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Counts
        context['pending_count'] = Referral.objects.filter(
            status='pending'
        ).count()
        context['in_progress_count'] = Referral.objects.filter(
            status='in_progress'
        ).count()

        return context


class ReferralCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new referral."""

    model = Referral
    template_name = 'admin/referrals/referral_form.html'
    permission_required = 'vet_clinic.add_referral'
    fields = [
        'direction', 'pet', 'specialist', 'reason', 'urgency',
        'diagnosis', 'requested_services', 'relevant_history', 'referred_date'
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Pre-fill pet if provided
        pet_id = self.request.GET.get('pet')
        if pet_id:
            form.fields['pet'].initial = pet_id

        return form

    def form_valid(self, form):
        form.instance.owner = form.instance.pet.owner
        form.instance.created_by = self.request.user
        form.instance.status = 'pending'

        response = super().form_valid(form)

        # Send referral
        if self.request.POST.get('send_now'):
            self._send_referral(self.object)

        return response

    def _send_referral(self, referral):
        """Send referral to specialist."""
        from apps.communications.tasks import send_referral_notification
        send_referral_notification.delay(referral.id)

        referral.status = 'sent'
        referral.sent_via = 'email'  # or whatsapp based on specialist preference
        referral.save()


class ReferralDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Referral detail with full history."""

    model = Referral
    template_name = 'admin/referrals/referral_detail.html'
    permission_required = 'vet_clinic.view_referral'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all()
        return context


class VisitingCalendarView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Calendar of visiting specialists."""

    model = VisitingSchedule
    template_name = 'admin/referrals/visiting_calendar.html'
    context_object_name = 'schedules'
    permission_required = 'vet_clinic.view_visitingschedule'

    def get_queryset(self):
        return VisitingSchedule.objects.filter(
            date__gte=timezone.now().date()
        ).select_related('specialist').order_by('date', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Group by date for calendar view
        from collections import defaultdict
        by_date = defaultdict(list)
        for schedule in self.object_list:
            by_date[schedule.date].append(schedule)
        context['schedules_by_date'] = dict(by_date)

        return context


class BookVisitingAppointmentView(LoginRequiredMixin, CreateView):
    """Book appointment with visiting specialist."""

    model = VisitingAppointment
    template_name = 'admin/referrals/book_visiting.html'
    fields = ['pet', 'start_time', 'service']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schedule'] = get_object_or_404(
            VisitingSchedule, pk=self.kwargs['schedule_pk']
        )
        return context

    def form_valid(self, form):
        schedule = get_object_or_404(
            VisitingSchedule, pk=self.kwargs['schedule_pk']
        )

        form.instance.schedule = schedule
        form.instance.owner = form.instance.pet.owner
        form.instance.end_time = form.cleaned_data['start_time']  # Calculate based on service duration

        response = super().form_valid(form)

        # Update schedule count
        schedule.appointments_booked += 1
        schedule.save()

        return response
```

#### Templates
```html
<!-- templates/admin/referrals/directory.html -->
{% extends "admin/base.html" %}
{% load i18n %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">{% trans 'Directorio de Especialistas' %}</h1>
        <a href="{% url 'admin:referrals:specialist_create' %}"
           class="btn btn-primary">
            + {% trans 'Agregar Especialista' %}
        </a>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
        <form method="get" class="flex flex-wrap gap-4">
            <input type="text" name="q" value="{{ request.GET.q }}"
                   placeholder="{% trans 'Buscar...' %}"
                   class="px-4 py-2 border rounded-lg">

            <select name="type" class="px-4 py-2 border rounded-lg">
                <option value="">{% trans 'Todos los tipos' %}</option>
                {% for value, label in partner_types %}
                <option value="{{ value }}"
                        {% if request.GET.type == value %}selected{% endif %}>
                    {{ label }}
                </option>
                {% endfor %}
            </select>

            <select name="specialty" class="px-4 py-2 border rounded-lg">
                <option value="">{% trans 'Todas las especialidades' %}</option>
                {% for specialty in specialties %}
                <option value="{{ specialty.slug }}"
                        {% if request.GET.specialty == specialty.slug %}selected{% endif %}>
                    {{ specialty.name }}
                </option>
                {% endfor %}
            </select>

            <button type="submit" class="btn btn-secondary">
                {% trans 'Filtrar' %}
            </button>
        </form>
    </div>

    <!-- Directory Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {% for specialist in specialists %}
        <div class="bg-white rounded-lg shadow hover:shadow-lg transition">
            <div class="p-6">
                <div class="flex justify-between items-start">
                    <div>
                        <h3 class="font-semibold text-lg">{{ specialist.name }}</h3>
                        <p class="text-gray-600">{{ specialist.get_partner_type_display }}</p>
                    </div>
                    {% if specialist.is_visiting %}
                    <span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                        {% trans 'Visitante' %}
                    </span>
                    {% endif %}
                </div>

                <div class="mt-4 space-y-2 text-sm">
                    <p class="flex items-center gap-2">
                        📍 {{ specialist.city }}
                        {% if specialist.distance_km %}
                        <span class="text-gray-500">({{ specialist.distance_km }} km)</span>
                        {% endif %}
                    </p>
                    <p class="flex items-center gap-2">
                        📞 {{ specialist.phone }}
                    </p>
                    {% if specialist.accepts_emergencies %}
                    <p class="text-red-600">🚨 {% trans 'Acepta emergencias' %}</p>
                    {% endif %}
                </div>

                {% if specialist.specialties.exists %}
                <div class="mt-4 flex flex-wrap gap-1">
                    {% for specialty in specialist.specialties.all %}
                    <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                        {{ specialty.name }}
                    </span>
                    {% endfor %}
                </div>
                {% endif %}

                <div class="mt-4 flex gap-2">
                    <a href="{% url 'admin:referrals:specialist_detail' specialist.pk %}"
                       class="btn btn-sm btn-secondary">
                        {% trans 'Ver' %}
                    </a>
                    <a href="{% url 'admin:referrals:referral_create' %}?specialist={{ specialist.pk }}"
                       class="btn btn-sm btn-primary">
                        {% trans 'Referir paciente' %}
                    </a>
                </div>
            </div>
        </div>
        {% empty %}
        <p class="col-span-full text-center py-12 text-gray-500">
            {% trans 'No se encontraron especialistas.' %}
        </p>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

### Test Cases
- [ ] Directory lists specialists
- [ ] Filtering works
- [ ] Specialist detail shows referrals
- [ ] Referral creation works
- [ ] Document upload works
- [ ] Visiting calendar displays
- [ ] Appointment booking works

### Definition of Done
- [ ] All views implemented
- [ ] Templates responsive
- [ ] HTMX interactions smooth
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-052: Referral Network Models
- T-002: Base Templates

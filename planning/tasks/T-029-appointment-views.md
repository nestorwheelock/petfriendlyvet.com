# T-029: Appointment Booking Views

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement appointment booking UI and calendar views
**Related Story**: S-004
**Epoch**: 2
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/appointments/views/, templates/appointments/
**Forbidden Paths**: apps/admin/

### Deliverables
- [ ] Appointment booking form
- [ ] Calendar date picker
- [ ] Time slot selection
- [ ] Booking confirmation page
- [ ] My appointments list
- [ ] Appointment detail view
- [ ] Cancel/reschedule UI

### Wireframe Reference
See: `planning/wireframes/05-appointment.txt`

### Implementation Details

#### Booking Flow
1. Select pet (or add new)
2. Select service type
3. Choose date (calendar)
4. Choose time slot
5. Add notes
6. Confirm

#### Views
```python
class AppointmentBookingView(LoginRequiredMixin, FormView):
    """Multi-step appointment booking."""

    template_name = 'appointments/booking.html'
    form_class = AppointmentBookingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pets'] = Pet.objects.filter(owner=self.request.user, is_active=True)
        context['services'] = ServiceType.objects.filter(is_bookable_online=True)
        return context


class AvailabilityAPIView(View):
    """HTMX endpoint for getting available slots."""

    def get(self, request):
        date = request.GET.get('date')
        service_id = request.GET.get('service')

        service = get_object_or_404(ServiceType, id=service_id)
        target_date = datetime.strptime(date, "%Y-%m-%d").date()

        slots = AvailabilityService().get_available_slots(target_date, service)

        return render(request, 'appointments/partials/time_slots.html', {
            'slots': slots,
            'date': target_date,
            'service': service
        })
```

#### Date Picker (Alpine.js)
```html
<div x-data="datePicker()" class="calendar">
    <div class="flex justify-between items-center mb-4">
        <button @click="prevMonth()" class="p-2">←</button>
        <span class="font-semibold" x-text="monthYear"></span>
        <button @click="nextMonth()" class="p-2">→</button>
    </div>

    <div class="grid grid-cols-7 gap-1">
        <!-- Day headers -->
        <template x-for="day in ['L', 'M', 'X', 'J', 'V', 'S', 'D']">
            <div class="text-center text-sm text-gray-500" x-text="day"></div>
        </template>

        <!-- Calendar days -->
        <template x-for="day in days">
            <button
                @click="selectDate(day)"
                :class="{
                    'bg-primary text-white': isSelected(day),
                    'bg-gray-100': !isAvailable(day),
                    'hover:bg-primary-light': isAvailable(day)
                }"
                :disabled="!isAvailable(day)"
                class="p-2 rounded"
                x-text="day.getDate()">
            </button>
        </template>
    </div>
</div>
```

#### Time Slots (HTMX)
```html
<!-- templates/appointments/partials/time_slots.html -->
<div class="grid grid-cols-3 gap-2">
    {% for slot in slots %}
    <button
        type="button"
        hx-post="{% url 'appointments:select_slot' %}"
        hx-vals='{"date": "{{ date|date:'Y-m-d' }}", "time": "{{ slot|time:'H:i' }}"}'
        hx-target="#booking-confirmation"
        class="p-3 border rounded-lg hover:bg-primary hover:text-white transition">
        {{ slot|time:"g:i A" }}
    </button>
    {% empty %}
    <p class="col-span-3 text-center text-gray-500 py-4">
        {% trans "No hay horarios disponibles para esta fecha" %}
    </p>
    {% endfor %}
</div>
```

#### Confirmation Component
```html
<div id="booking-confirmation" class="bg-green-50 p-6 rounded-xl">
    <div class="flex items-center gap-4 mb-4">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            ✓
        </div>
        <div>
            <h3 class="text-lg font-semibold">{% trans "Cita Solicitada" %}</h3>
            <p class="text-gray-600">{% trans "Te confirmaremos pronto" %}</p>
        </div>
    </div>

    <div class="space-y-2">
        <p><strong>🐾 Mascota:</strong> {{ appointment.pet.name }}</p>
        <p><strong>🏥 Servicio:</strong> {{ appointment.service.name }}</p>
        <p><strong>📅 Fecha:</strong> {{ appointment.scheduled_date|date:"l, d F Y" }}</p>
        <p><strong>🕐 Hora:</strong> {{ appointment.scheduled_time|time:"g:i A" }}</p>
    </div>

    <div class="mt-6 flex gap-4">
        <a href="{% url 'appointments:my_appointments' %}" class="btn btn-primary">
            {% trans "Ver mis citas" %}
        </a>
        <a href="{% url 'home' %}" class="btn btn-secondary">
            {% trans "Inicio" %}
        </a>
    </div>
</div>
```

#### My Appointments List
```html
<div class="space-y-4">
    {% for appointment in appointments %}
    <div class="bg-white rounded-xl shadow p-4 flex items-center gap-4">
        <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
            {{ appointment.pet.species_emoji }}
        </div>
        <div class="flex-grow">
            <h3 class="font-semibold">{{ appointment.pet.name }} - {{ appointment.service.name }}</h3>
            <p class="text-sm text-gray-600">
                {{ appointment.scheduled_date|date:"D, d M" }} a las {{ appointment.scheduled_time|time:"g:i A" }}
            </p>
        </div>
        <div class="text-right">
            <span class="px-2 py-1 rounded text-sm
                {% if appointment.status == 'confirmed' %}bg-green-100 text-green-800
                {% elif appointment.status == 'requested' %}bg-yellow-100 text-yellow-800
                {% else %}bg-gray-100 text-gray-800{% endif %}">
                {{ appointment.get_status_display }}
            </span>
        </div>
    </div>
    {% endfor %}
</div>
```

### Test Cases
- [ ] Booking form validates
- [ ] Calendar shows available dates
- [ ] Time slots load via HTMX
- [ ] Confirmation displays correctly
- [ ] My appointments lists correctly
- [ ] Cancel/reschedule work
- [ ] Mobile layout correct

### Definition of Done
- [ ] Full booking flow working
- [ ] Calendar responsive
- [ ] HTMX interactions smooth
- [ ] Bilingual content
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-027: Appointment Models
- T-028: AI Booking Tools
- T-002: Base Templates

# T-026: Pet Profile Views & Dashboard

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement pet profile dashboard for owners
**Related Story**: S-003
**Epoch**: 2
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/vet_clinic/views/, templates/vet_clinic/
**Forbidden Paths**: apps/admin/

### Deliverables
- [ ] Pet list view (owner's pets)
- [ ] Pet detail/profile page
- [ ] Medical history timeline
- [ ] Vaccination schedule
- [ ] Weight chart
- [ ] Pet edit form
- [ ] Add pet flow

### Wireframe Reference
See: `planning/wireframes/11-pet-profile.txt`

### Implementation Details

#### Pet Dashboard View
```python
class PetDashboardView(LoginRequiredMixin, DetailView):
    """Pet profile dashboard for owners."""

    model = Pet
    template_name = 'vet_clinic/pet_dashboard.html'
    context_object_name = 'pet'

    def get_queryset(self):
        """Only allow owner to view their pets."""
        return Pet.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pet = self.object

        # Recent medical records (last 5)
        context['recent_records'] = pet.medical_records.all()[:5]

        # Upcoming vaccinations
        context['upcoming_vaccinations'] = pet.vaccinations.filter(
            next_due_date__gte=timezone.now().date()
        ).order_by('next_due_date')[:3]

        # Overdue vaccinations
        context['overdue_vaccinations'] = pet.vaccinations.filter(
            next_due_date__lt=timezone.now().date()
        )

        # Weight history for chart
        context['weight_history'] = list(
            pet.weight_history.order_by('date').values('date', 'weight_kg')
        )

        # Active conditions
        context['active_conditions'] = pet.conditions.filter(
            status__in=['active', 'managed']
        )

        # Allergies
        context['allergies'] = pet.allergies.all()

        return context
```

#### Pet List View (Owner's Pets)
```python
class MyPetsView(LoginRequiredMixin, ListView):
    """List all pets for the logged-in owner."""

    model = Pet
    template_name = 'vet_clinic/my_pets.html'
    context_object_name = 'pets'

    def get_queryset(self):
        return Pet.objects.filter(
            owner=self.request.user,
            is_active=True
        ).order_by('name')
```

#### Pet Creation Flow
```python
class AddPetView(LoginRequiredMixin, CreateView):
    """Add a new pet for the logged-in owner."""

    model = Pet
    form_class = PetForm
    template_name = 'vet_clinic/add_pet.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vet_clinic:pet_dashboard', kwargs={'pk': self.object.pk})
```

#### Templates

**Pet Card Component**
```html
<!-- templates/vet_clinic/components/pet_card.html -->
<div class="bg-white rounded-xl shadow-md overflow-hidden">
    <div class="flex">
        <div class="w-24 h-24 flex-shrink-0">
            {% if pet.photo %}
                <img src="{{ pet.photo.url }}" alt="{{ pet.name }}" class="w-full h-full object-cover">
            {% else %}
                <div class="w-full h-full bg-gray-200 flex items-center justify-center">
                    <span class="text-4xl">{{ pet.species_emoji }}</span>
                </div>
            {% endif %}
        </div>
        <div class="p-4 flex-grow">
            <h3 class="text-lg font-semibold">{{ pet.name }}</h3>
            <p class="text-gray-600">{{ pet.breed|default:"Mestizo" }}</p>
            <p class="text-sm text-gray-500">{{ pet.age }}</p>
        </div>
        <div class="p-4">
            <a href="{% url 'vet_clinic:pet_dashboard' pet.pk %}"
               class="text-primary hover:text-primary-dark">
                Ver →
            </a>
        </div>
    </div>
</div>
```

**Weight Chart (Alpine.js + Chart.js)**
```html
<div x-data="weightChart({{ weight_history|safe }})" class="h-64">
    <canvas x-ref="chart"></canvas>
</div>

<script>
function weightChart(data) {
    return {
        init() {
            new Chart(this.$refs.chart, {
                type: 'line',
                data: {
                    labels: data.map(d => d.date),
                    datasets: [{
                        label: 'Peso (kg)',
                        data: data.map(d => d.weight_kg),
                        borderColor: '#10B981',
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }
}
</script>
```

**Vaccination Timeline**
```html
<div class="space-y-4">
    {% for vacc in upcoming_vaccinations %}
    <div class="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
        <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
            💉
        </div>
        <div class="flex-grow">
            <p class="font-medium">{{ vacc.vaccine_name }}</p>
            <p class="text-sm text-gray-600">
                {% trans "Próxima:" %} {{ vacc.next_due_date|date:"d M Y" }}
            </p>
        </div>
        <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
            {% trans "Programada" %}
        </span>
    </div>
    {% endfor %}
</div>
```

### Test Cases
- [ ] Owner can view their pets only
- [ ] Pet dashboard loads correctly
- [ ] Medical history displays
- [ ] Vaccination schedule accurate
- [ ] Weight chart renders
- [ ] Add pet form works
- [ ] Photo upload works
- [ ] Mobile layout correct

### Definition of Done
- [ ] All views implemented
- [ ] Dashboard comprehensive
- [ ] Mobile-optimized
- [ ] Bilingual content
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-024: Pet Profile Models
- T-025: Medical Records Models
- T-002: Base Templates

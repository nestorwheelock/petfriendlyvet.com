# T-048: Unified Communications Inbox

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement unified inbox for all communication channels
**Related Story**: S-006
**Epoch**: 4
**Estimate**: 5 hours

### Constraints
**Allowed File Paths**: apps/communications/, templates/admin/inbox/
**Forbidden Paths**: None

### Deliverables
- [ ] Inbox views (list, detail)
- [ ] Conversation management
- [ ] Reply functionality (multi-channel)
- [ ] Assignment and status
- [ ] Real-time updates (HTMX)
- [ ] Mobile-responsive interface

### Wireframe Reference
See: `planning/wireframes/16-communications-inbox.txt`

### Implementation Details

#### Views
```python
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class InboxView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Unified inbox for staff."""

    model = Conversation
    template_name = 'admin/inbox/inbox.html'
    context_object_name = 'conversations'
    permission_required = 'communications.view_conversation'
    paginate_by = 25

    def get_queryset(self):
        queryset = Conversation.objects.select_related(
            'owner', 'assigned_to', 'pet'
        ).prefetch_related('messages')

        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        else:
            queryset = queryset.exclude(status='archived')

        # Priority filter
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Assignment filter
        assigned = self.request.GET.get('assigned')
        if assigned == 'me':
            queryset = queryset.filter(assigned_to=self.request.user)
        elif assigned == 'unassigned':
            queryset = queryset.filter(assigned_to__isnull=True)

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(owner__first_name__icontains=search) |
                Q(owner__last_name__icontains=search) |
                Q(owner__email__icontains=search) |
                Q(subject__icontains=search) |
                Q(messages__body__icontains=search)
            ).distinct()

        return queryset.order_by('-last_message_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Counts for tabs
        context['counts'] = {
            'all': Conversation.objects.exclude(status='archived').count(),
            'pending': Conversation.objects.filter(status='pending').count(),
            'mine': Conversation.objects.filter(
                assigned_to=self.request.user
            ).exclude(status='archived').count(),
            'unread': Conversation.objects.filter(unread_count__gt=0).count(),
        }

        context['staff_users'] = User.objects.filter(
            is_staff=True
        ).order_by('first_name')

        return context


class ConversationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View conversation and send replies."""

    model = Conversation
    template_name = 'admin/inbox/conversation.html'
    context_object_name = 'conversation'
    permission_required = 'communications.view_conversation'

    def get_queryset(self):
        return Conversation.objects.select_related(
            'owner', 'assigned_to', 'pet', 'appointment', 'order'
        ).prefetch_related(
            'messages__channel'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.object

        # Mark as read
        if conversation.unread_count > 0:
            conversation.unread_count = 0
            conversation.save()

        # Get available channels for reply
        context['channels'] = Channel.objects.filter(is_active=True)

        # Owner's contact preferences
        if conversation.owner:
            context['preferences'] = ContactPreference.objects.filter(
                owner=conversation.owner
            ).first()

        # Related info
        if conversation.pet:
            context['pet'] = conversation.pet
        if conversation.owner:
            context['pets'] = conversation.owner.pets.all()
            context['appointments'] = conversation.owner.appointments.filter(
                status__in=['scheduled', 'confirmed']
            )[:5]
            context['orders'] = conversation.owner.orders.all()[:5]

        # Templates for quick replies
        context['templates'] = MessageTemplate.objects.filter(
            is_active=True
        ).order_by('name')

        return context

    def post(self, request, *args, **kwargs):
        """Send reply."""
        self.object = self.get_object()

        channel_id = request.POST.get('channel')
        body = request.POST.get('body')
        template_id = request.POST.get('template')

        channel = Channel.objects.get(id=channel_id)

        # Get template if specified
        template = None
        if template_id:
            template = MessageTemplate.objects.get(id=template_id)
            body = template.body_text

        # Create message
        message = Message.objects.create(
            conversation=self.object,
            channel=channel,
            direction='outbound',
            from_user=request.user,
            to_contact=self._get_contact_for_channel(channel),
            body=body,
            template=template,
            status='pending'
        )

        # Send via appropriate service
        self._send_message(message, channel)

        # Update conversation
        self.object.last_message_at = timezone.now()
        self.object.last_staff_message_at = timezone.now()
        self.object.status = 'active'
        self.object.save()

        if request.htmx:
            return render(request, 'admin/inbox/_message.html', {
                'message': message
            })

        return redirect('inbox:conversation', pk=self.object.pk)

    def _get_contact_for_channel(self, channel):
        """Get appropriate contact info for channel."""
        owner = self.object.owner

        if not owner:
            return ''

        pref = ContactPreference.objects.filter(owner=owner).first()

        if channel.channel_type == 'email':
            return pref.email if pref else owner.email
        elif channel.channel_type == 'sms':
            return pref.phone if pref else ''
        elif channel.channel_type == 'whatsapp':
            return pref.whatsapp if pref else pref.phone if pref else ''

        return ''

    def _send_message(self, message, channel):
        """Send message via channel."""
        from apps.communications.tasks import send_message_task

        send_message_task.delay(message.id)


class AssignConversationView(LoginRequiredMixin, View):
    """Assign conversation to staff member."""

    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        user_id = request.POST.get('user_id')

        if user_id:
            conversation.assigned_to_id = user_id
        else:
            conversation.assigned_to = None

        conversation.save()

        if request.htmx:
            return render(request, 'admin/inbox/_assignment.html', {
                'conversation': conversation
            })

        return redirect('inbox:conversation', pk=pk)


class UpdateStatusView(LoginRequiredMixin, View):
    """Update conversation status."""

    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        status = request.POST.get('status')

        if status in dict(Conversation.STATUS_CHOICES):
            conversation.status = status
            conversation.save()

        if request.htmx:
            return render(request, 'admin/inbox/_status.html', {
                'conversation': conversation
            })

        return redirect('inbox:conversation', pk=pk)
```

#### Templates
```html
<!-- templates/admin/inbox/inbox.html -->
{% extends "admin/base.html" %}
{% load i18n %}

{% block content %}
<div class="flex h-screen" x-data="inbox()">

    <!-- Sidebar - Conversation List -->
    <aside class="w-96 border-r bg-gray-50 flex flex-col">
        <!-- Header -->
        <div class="p-4 border-b bg-white">
            <h1 class="text-xl font-bold">{% trans 'Bandeja de entrada' %}</h1>
            <input type="search"
                   placeholder="{% trans 'Buscar...' %}"
                   class="w-full mt-2 px-3 py-2 border rounded-lg"
                   hx-get="{% url 'inbox:inbox' %}"
                   hx-trigger="keyup changed delay:300ms"
                   hx-target="#conversation-list"
                   name="q">
        </div>

        <!-- Tabs -->
        <div class="flex border-b bg-white text-sm">
            <a href="?status="
               class="flex-1 py-2 text-center {% if not request.GET.status %}border-b-2 border-primary{% endif %}">
                {% trans 'Todos' %} ({{ counts.all }})
            </a>
            <a href="?status=pending"
               class="flex-1 py-2 text-center {% if request.GET.status == 'pending' %}border-b-2 border-primary{% endif %}">
                {% trans 'Pendientes' %} ({{ counts.pending }})
            </a>
            <a href="?assigned=me"
               class="flex-1 py-2 text-center {% if request.GET.assigned == 'me' %}border-b-2 border-primary{% endif %}">
                {% trans 'Míos' %} ({{ counts.mine }})
            </a>
        </div>

        <!-- Conversation List -->
        <div id="conversation-list" class="flex-1 overflow-y-auto">
            {% for conv in conversations %}
            <a href="{% url 'inbox:conversation' conv.pk %}"
               class="block p-4 border-b hover:bg-white {% if conv.unread_count %}bg-blue-50{% endif %}"
               hx-get="{% url 'inbox:conversation' conv.pk %}"
               hx-target="#conversation-detail"
               hx-push-url="true">

                <div class="flex justify-between items-start">
                    <div class="flex items-center gap-2">
                        {% if conv.unread_count %}
                        <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                        {% endif %}
                        <span class="font-medium">
                            {{ conv.owner.get_full_name|default:conv.subject }}
                        </span>
                    </div>
                    <span class="text-xs text-gray-500">
                        {{ conv.last_message_at|timesince }} ago
                    </span>
                </div>

                <p class="text-sm text-gray-600 truncate mt-1">
                    {{ conv.messages.last.body|truncatechars:50 }}
                </p>

                <div class="flex gap-2 mt-2">
                    {% if conv.pet %}
                    <span class="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
                        🐾 {{ conv.pet.name }}
                    </span>
                    {% endif %}
                    <span class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                        {{ conv.messages.last.channel.get_channel_type_display }}
                    </span>
                </div>
            </a>
            {% empty %}
            <p class="p-8 text-center text-gray-500">
                {% trans 'No hay conversaciones' %}
            </p>
            {% endfor %}
        </div>
    </aside>

    <!-- Main - Conversation Detail -->
    <main id="conversation-detail" class="flex-1 flex flex-col">
        {% if conversation %}
        {% include "admin/inbox/_conversation_detail.html" %}
        {% else %}
        <div class="flex-1 flex items-center justify-center text-gray-500">
            {% trans 'Selecciona una conversación' %}
        </div>
        {% endif %}
    </main>

    <!-- Right Sidebar - Context -->
    <aside class="w-80 border-l bg-gray-50 overflow-y-auto">
        {% if conversation and conversation.owner %}
        <div class="p-4">
            <h3 class="font-semibold mb-4">{% trans 'Cliente' %}</h3>

            <div class="bg-white rounded-lg p-4 shadow-sm">
                <p class="font-medium">{{ conversation.owner.get_full_name }}</p>
                <p class="text-sm text-gray-600">{{ conversation.owner.email }}</p>
                <p class="text-sm text-gray-600">{{ preferences.phone }}</p>
            </div>

            {% if pets %}
            <h4 class="font-semibold mt-4 mb-2">{% trans 'Mascotas' %}</h4>
            {% for pet in pets %}
            <div class="bg-white rounded-lg p-3 shadow-sm mb-2">
                <p class="font-medium">{{ pet.name }}</p>
                <p class="text-sm text-gray-600">{{ pet.species }} • {{ pet.breed }}</p>
            </div>
            {% endfor %}
            {% endif %}

            {% if appointments %}
            <h4 class="font-semibold mt-4 mb-2">{% trans 'Próximas citas' %}</h4>
            {% for apt in appointments %}
            <div class="bg-white rounded-lg p-3 shadow-sm mb-2">
                <p class="text-sm">{{ apt.service.name }}</p>
                <p class="text-xs text-gray-600">{{ apt.start_time|date:"d M, H:i" }}</p>
            </div>
            {% endfor %}
            {% endif %}
        </div>
        {% endif %}
    </aside>
</div>
{% endblock %}
```

### Test Cases
- [ ] Inbox lists conversations
- [ ] Filtering works
- [ ] Search works
- [ ] Conversation detail loads
- [ ] Reply sends via correct channel
- [ ] Assignment works
- [ ] Status updates work
- [ ] Real-time updates (HTMX)

### Definition of Done
- [ ] Inbox fully functional
- [ ] Mobile responsive
- [ ] Multi-channel reply works
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-044: Communication Channel Models
- T-045: Email Integration
- T-046: SMS Integration
- T-047: WhatsApp Integration

"""Views for AI assistant functionality."""
import json
import uuid

from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .services import AIService
from .models import Conversation, Message
from .tools import ToolRegistry, handle_tool_calls


QUICK_ACTIONS = [
    {'key': 'hours', 'es': '¿Cuál es su horario?', 'en': 'What are your hours?'},
    {'key': 'appointment', 'es': 'Quiero agendar una cita', 'en': 'I want to book an appointment'},
    {'key': 'services', 'es': '¿Qué servicios ofrecen?', 'en': 'What services do you offer?'},
    {'key': 'contact', 'es': 'Información de contacto', 'en': 'Contact information'},
]


ADMIN_QUICK_COMMANDS = [
    {'label': "Today's appointments", 'command': "show today's appointments"},
    {'label': "Low stock items", 'command': "show products with low stock"},
    {'label': "Pending invoices", 'command': "show unpaid invoices"},
    {'label': "Recent messages", 'command': "show unread messages"},
    {'label': "Add new pet", 'command': "I need to add a new pet"},
    {'label': "Search client", 'command': "search for client"},
]


def is_staff_or_admin(user):
    """Check if user has staff or admin role."""
    if not user.is_authenticated:
        return False
    role = getattr(user, 'role', 'customer')
    return role in ['staff', 'admin'] or user.is_staff or user.is_superuser


class ChatView(View):
    """Handle chat messages from the widget."""

    def post(self, request):
        """Process a chat message and return AI response."""
        try:
            # Parse request body
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            message = data.get('message', '').strip()
            session_id = data.get('session_id', str(uuid.uuid4()))
            language = data.get('language', 'es')

            if not message:
                return JsonResponse({
                    'error': True,
                    'message': 'Message is required'
                }, status=400)

            # Get or create conversation
            conversation, created = Conversation.objects.get_or_create(
                session_id=session_id,
                defaults={
                    'user': request.user if request.user.is_authenticated else None,
                    'language': language,
                }
            )

            # Save user message
            Message.objects.create(
                conversation=conversation,
                role='user',
                content=message
            )

            # Get AI response
            ai_service = AIService(
                user=request.user if request.user.is_authenticated else None,
                language=language
            )

            # Get response synchronously for now
            response_text = ai_service.get_response_sync(message)

            # Save assistant message
            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=response_text
            )

            return JsonResponse({
                'success': True,
                'response': response_text,
                'session_id': session_id
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'error': True,
                'message': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': True,
                'message': str(e)
            }, status=500)

    def get(self, request):
        """GET not allowed for chat endpoint."""
        return JsonResponse({
            'error': True,
            'message': 'Method not allowed'
        }, status=405)


chat_view = ChatView.as_view()


def get_quick_actions(request):
    """Return available quick actions."""
    language = request.GET.get('language', 'es')
    actions = []
    for action in QUICK_ACTIONS:
        actions.append({
            'key': action['key'],
            'text': action.get(language, action['es'])
        })
    return JsonResponse({'actions': actions})


def get_chat_history(request):
    """Return chat history for a session."""
    session_id = request.GET.get('session_id')

    if not session_id:
        return JsonResponse({'messages': []})

    try:
        conversation = Conversation.objects.get(session_id=session_id)
        messages = conversation.messages.order_by('created_at').values(
            'role', 'content', 'created_at'
        )
        return JsonResponse({
            'messages': list(messages)
        })
    except Conversation.DoesNotExist:
        return JsonResponse({'messages': []})


class AdminChatView(LoginRequiredMixin, View):
    """Admin chat interface with elevated permissions."""
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        """Check staff/admin permission before dispatch."""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_staff_or_admin(request.user):
            return HttpResponseForbidden("Access denied")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Render admin chat page."""
        return render(request, 'ai_assistant/admin_chat.html', {
            'quick_commands': ADMIN_QUICK_COMMANDS,
            'user': request.user,
        })


admin_chat_view = AdminChatView.as_view()


class AdminChatAPIView(LoginRequiredMixin, View):
    """Admin chat API with tool execution visibility."""
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        """Check staff/admin permission before dispatch."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': True, 'message': 'Authentication required'}, status=403)
        if not is_staff_or_admin(request.user):
            return JsonResponse({'error': True, 'message': 'Access denied'}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        """Process admin chat message with tool visibility."""
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            message = data.get('message', '').strip()
            session_id = data.get('session_id', f'admin_{request.user.id}_{uuid.uuid4().hex[:8]}')
            language = data.get('language', 'es')

            if not message:
                return JsonResponse({
                    'error': True,
                    'message': 'Message is required'
                }, status=400)

            # Get or create conversation
            conversation, created = Conversation.objects.get_or_create(
                session_id=session_id,
                defaults={
                    'user': request.user,
                    'language': language,
                }
            )

            # Save user message
            Message.objects.create(
                conversation=conversation,
                role='user',
                content=message
            )

            # Get AI response with elevated permissions
            ai_service = AIService(
                user=request.user,
                language=language
            )

            response_text = ai_service.get_response_sync(message)

            # Save assistant message
            Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=response_text
            )

            # For admin, include tool execution info
            tools_used = []  # Would be populated from actual tool calls
            available_tools = ToolRegistry.get_tools_for_user(request.user)

            return JsonResponse({
                'success': True,
                'response': response_text,
                'session_id': session_id,
                'tools_available': len(available_tools),
                'tools_used': tools_used,
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'error': True,
                'message': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': True,
                'message': str(e)
            }, status=500)


admin_chat_api_view = AdminChatAPIView.as_view()


@login_required
def conversation_list(request):
    """List all conversations for admin/staff."""
    if not is_staff_or_admin(request.user):
        return HttpResponseForbidden("Access denied")

    conversations = Conversation.objects.all().order_by('-updated_at')[:50]

    if request.headers.get('Accept') == 'application/json':
        data = []
        for conv in conversations:
            data.append({
                'id': conv.id,
                'session_id': conv.session_id,
                'user': conv.user.username if conv.user else 'Anonymous',
                'language': conv.language,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'message_count': conv.messages.count(),
            })
        return JsonResponse({'conversations': data})

    return render(request, 'ai_assistant/conversation_list.html', {
        'conversations': conversations,
    })

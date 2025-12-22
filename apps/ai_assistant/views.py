"""Views for AI assistant functionality."""
import json
import uuid

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

from .services import AIService
from .models import Conversation, Message
from .tools import ToolRegistry, handle_tool_calls


QUICK_ACTIONS = [
    {'key': 'hours', 'es': '¿Cuál es su horario?', 'en': 'What are your hours?'},
    {'key': 'appointment', 'es': 'Quiero agendar una cita', 'en': 'I want to book an appointment'},
    {'key': 'services', 'es': '¿Qué servicios ofrecen?', 'en': 'What services do you offer?'},
    {'key': 'contact', 'es': 'Información de contacto', 'en': 'Contact information'},
]


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

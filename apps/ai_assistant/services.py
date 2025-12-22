"""High-level AI service for the Pet-Friendly Vet application."""
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .clients import OpenRouterClient


class AIService:
    """High-level AI service for the application."""

    def __init__(self, user=None, language='es'):
        """Initialize AI service.

        Args:
            user: Optional Django user object for context
            language: Language code (es, en, etc.)
        """
        self.client = OpenRouterClient()
        self.user = user
        self.language = language
        self.conversation = None

    def build_system_prompt(self) -> str:
        """Build system prompt with context and language.

        Returns:
            System prompt string for Claude
        """
        if self.language == 'en':
            return """You are a helpful AI assistant for Pet-Friendly Veterinary Clinic in Puerto Morelos, Mexico.

Your role is to:
- Answer questions about the clinic, services, and hours
- Help schedule appointments
- Provide general pet care advice
- Assist with product inquiries from the store

About the clinic:
- Name: Pet-Friendly Veterinary Clinic
- Location: Puerto Morelos, Quintana Roo, Mexico
- Hours: Tuesday-Sunday 9am-8pm (Closed Monday)
- Phone: +52 998 316 2438
- Services: Clinic, Pharmacy, Pet Store

Be friendly, helpful, and professional. If you don't know something, admit it and suggest contacting the clinic directly."""
        else:
            return """Eres un asistente virtual amigable para la Clínica Veterinaria Pet-Friendly en Puerto Morelos, México.

Tu rol es:
- Responder preguntas sobre la clínica, servicios y horarios
- Ayudar a agendar citas
- Proporcionar consejos generales sobre el cuidado de mascotas
- Asistir con consultas de productos de la tienda

Sobre la clínica:
- Nombre: Veterinaria Pet-Friendly
- Ubicación: Puerto Morelos, Quintana Roo, México
- Horario: Martes-Domingo 9am-8pm (Lunes cerrado)
- Teléfono: +52 998 316 2438
- Servicios: Clínica, Farmacia, Tienda de Mascotas

Sé amable, servicial y profesional. Si no sabes algo, admítelo y sugiere contactar directamente a la clínica."""

    async def get_response(
        self,
        user_message: str,
        context: dict = None,
    ) -> str:
        """Get AI response with full tool handling.

        Args:
            user_message: The user's message
            context: Optional additional context

        Returns:
            AI assistant's response string
        """
        messages = [
            {'role': 'system', 'content': self.build_system_prompt()},
            {'role': 'user', 'content': user_message}
        ]

        response = await self.client.chat(messages)

        if response.get('error'):
            return self._get_fallback_response()

        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError):
            return self._get_fallback_response()

    def get_response_sync(
        self,
        user_message: str,
        context: dict = None,
    ) -> str:
        """Synchronous version of get_response."""
        messages = [
            {'role': 'system', 'content': self.build_system_prompt()},
            {'role': 'user', 'content': user_message}
        ]

        response = self.client.chat_sync(messages)

        if response.get('error'):
            return self._get_fallback_response()

        try:
            return response['choices'][0]['message']['content']
        except (KeyError, IndexError):
            return self._get_fallback_response()

    def _get_fallback_response(self) -> str:
        """Return fallback response when AI is unavailable."""
        if self.language == 'en':
            return ("I'm sorry, I'm having trouble connecting right now. "
                    "Please contact us directly at +52 998 316 2438 or via WhatsApp.")
        else:
            return ("Lo siento, estoy teniendo problemas para conectar en este momento. "
                    "Por favor contáctenos directamente al +52 998 316 2438 o por WhatsApp.")

    def get_available_tools(self) -> list[dict]:
        """Get tools available based on user permissions.

        Returns:
            List of tool definitions for Claude
        """
        tools = [
            {
                'type': 'function',
                'function': {
                    'name': 'get_business_hours',
                    'description': 'Get the clinic business hours',
                    'parameters': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_services',
                    'description': 'Get list of clinic services',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'category': {
                                'type': 'string',
                                'description': 'Service category (clinic, pharmacy, store)',
                                'enum': ['clinic', 'pharmacy', 'store', 'all']
                            }
                        },
                        'required': []
                    }
                }
            }
        ]

        if self.user and self.user.is_authenticated:
            tools.append({
                'type': 'function',
                'function': {
                    'name': 'schedule_appointment',
                    'description': 'Schedule an appointment at the clinic',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'date': {
                                'type': 'string',
                                'description': 'Preferred date (YYYY-MM-DD)'
                            },
                            'time': {
                                'type': 'string',
                                'description': 'Preferred time (HH:MM)'
                            },
                            'service': {
                                'type': 'string',
                                'description': 'Type of service needed'
                            },
                            'pet_name': {
                                'type': 'string',
                                'description': 'Name of the pet'
                            }
                        },
                        'required': ['date', 'service']
                    }
                }
            })

        return tools

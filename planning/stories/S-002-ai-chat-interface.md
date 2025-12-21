# S-002: AI Chat Interface

**Story Type:** User Story
**Priority:** Critical
**Epoch:** 1
**Status:** PENDING

## User Story

**As a** pet owner visiting the website
**I want to** chat with an AI assistant in natural language
**So that** I can get information about the clinic, services, and pet care without navigating menus

## Acceptance Criteria

### Chat Interface (Customer)
- [ ] Chat widget visible on all pages (bottom-right corner)
- [ ] Chat opens in a slide-out panel or modal
- [ ] Input field supports text entry
- [ ] Messages display in conversation format
- [ ] AI responses stream in real-time (typing indicator)
- [ ] Chat history persists during session
- [ ] Language matches site language preference

### Chat Interface (Admin)
- [ ] Admin has separate chat interface with elevated tools
- [ ] Admin can search across all data
- [ ] Admin can perform CRUD operations via chat
- [ ] Admin chat accessible from custom dashboard

### AI Behavior
- [ ] Responds in the user's language (ES or EN)
- [ ] Provides accurate clinic information
- [ ] Answers pet care questions from knowledge base
- [ ] Gracefully handles unknown questions
- [ ] Escalates to human contact when appropriate
- [ ] Maintains conversation context

### Mobile Experience
- [ ] Chat works on mobile devices
- [ ] Touch-friendly interface
- [ ] Keyboard doesn't obscure input
- [ ] Smooth scrolling in chat history

## Example Conversations

### Information Query (Spanish)
```
Usuario: ¿A qué hora abren?
AI: ¡Hola! Pet-Friendly está abierto de martes a domingo, de 9:00am a 8:00pm.
    Los lunes estamos cerrados. ¿Hay algo más en lo que pueda ayudarte?

Usuario: ¿Tienen servicio de emergencia?
AI: Sí, ofrecemos servicios de emergencia. Para emergencias fuera del horario
    regular, puedes contactarnos por WhatsApp al +52 998 316 2438. El Dr. Pablo
    responde lo más pronto posible.
```

### Pet Care Question (English)
```
User: My dog has been scratching a lot lately
AI: I understand that can be concerning! Excessive scratching in dogs can have
    several causes including fleas, allergies, dry skin, or skin infections.

    Here are some questions that might help:
    - Have you noticed any fleas or flea dirt?
    - Has there been a change in diet or environment recently?
    - Is the scratching localized or all over?

    I'd recommend scheduling a consultation with Dr. Pablo to properly diagnose
    the issue. Would you like information about booking an appointment?
```

### Graceful Fallback
```
User: Can you prescribe medication for my cat?
AI: I'm not able to prescribe medications - only Dr. Pablo can do that after
    examining your cat. However, I can help you schedule an appointment, or
    you can contact us directly via WhatsApp at +52 998 316 2438.

    Would you like to book a consultation?
```

## Technical Requirements

### Frontend Components

```html
<!-- Chat Widget (Alpine.js) -->
<div x-data="chatWidget()" class="fixed bottom-4 right-4 z-50">
    <!-- Closed state: floating button -->
    <button @click="open = true" x-show="!open"
            class="bg-blue-600 text-white rounded-full p-4 shadow-lg">
        <svg><!-- chat icon --></svg>
    </button>

    <!-- Open state: chat panel -->
    <div x-show="open" x-transition
         class="bg-white rounded-lg shadow-xl w-80 md:w-96 h-[500px] flex flex-col">
        <!-- Header -->
        <div class="bg-blue-600 text-white p-4 rounded-t-lg flex justify-between">
            <span>Pet-Friendly Assistant</span>
            <button @click="open = false">×</button>
        </div>

        <!-- Messages -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4" x-ref="messages">
            <template x-for="msg in messages">
                <div :class="msg.role === 'user' ? 'text-right' : 'text-left'">
                    <div :class="msg.role === 'user' ? 'bg-blue-100' : 'bg-gray-100'"
                         class="inline-block p-3 rounded-lg max-w-[80%]">
                        <span x-text="msg.content"></span>
                    </div>
                </div>
            </template>
        </div>

        <!-- Input -->
        <form @submit.prevent="sendMessage" class="p-4 border-t">
            <div class="flex gap-2">
                <input x-model="input" type="text"
                       placeholder="Type a message..."
                       class="flex-1 border rounded-lg px-3 py-2">
                <button type="submit" class="bg-blue-600 text-white px-4 rounded-lg">
                    Send
                </button>
            </div>
        </form>
    </div>
</div>
```

### Backend Endpoint

```python
# views.py
@require_POST
def chat_message(request):
    """Handle incoming chat messages via HTMX"""
    message = request.POST.get('message')
    conversation_id = request.session.get('conversation_id')
    language = get_language()

    # Get or create conversation
    conversation = get_or_create_conversation(request, conversation_id)

    # Save user message
    Message.objects.create(
        conversation=conversation,
        role='user',
        content=message
    )

    # Get AI response with tool calling
    response = ai_service.get_response(
        conversation=conversation,
        message=message,
        language=language,
        tools=get_available_tools(request.user)
    )

    # Save assistant message
    Message.objects.create(
        conversation=conversation,
        role='assistant',
        content=response.content,
        tool_calls=response.tool_calls
    )

    return JsonResponse({
        'content': response.content,
        'conversation_id': conversation.id
    })
```

### AI Service

```python
# services/ai.py
class AIService:
    def __init__(self):
        self.client = OpenRouter(api_key=settings.OPENROUTER_API_KEY)

    def get_response(self, conversation, message, language, tools):
        # Build conversation history
        messages = self._build_messages(conversation, language)
        messages.append({"role": "user", "content": message})

        # Call AI with tools
        response = self.client.chat.completions.create(
            model="anthropic/claude-3-5-sonnet",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        # Process tool calls if any
        if response.tool_calls:
            tool_results = self._execute_tools(response.tool_calls)
            # Get final response with tool results
            response = self._get_final_response(messages, tool_results)

        return response

    def _build_messages(self, conversation, language):
        system_prompt = self._get_system_prompt(language)
        history = conversation.messages.order_by('created_at')[:20]

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def _get_system_prompt(self, language):
        if language == 'es':
            return """Eres el asistente virtual de Pet-Friendly, la clínica
            veterinaria del Dr. Pablo en Puerto Morelos. Responde en español
            de manera amigable y profesional. Ayuda con información sobre
            la clínica, servicios, horarios, y preguntas sobre cuidado de mascotas."""
        else:
            return """You are the virtual assistant for Pet-Friendly,
            Dr. Pablo's veterinary clinic in Puerto Morelos. Respond in English
            in a friendly and professional manner. Help with clinic information,
            services, hours, and pet care questions."""
```

## Definition of Done

- [ ] Chat widget renders on all pages
- [ ] Messages send and receive correctly
- [ ] AI responds appropriately in both languages
- [ ] Tool calling works for clinic info queries
- [ ] Chat history maintains during session
- [ ] Mobile experience is smooth
- [ ] Streaming responses implemented
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation updated

## Dependencies

- S-001: Foundation + AI Core (must be complete)
- OpenRouter API access
- Knowledge base seeded with content

## Notes

- In Epoch 1, chat is informational only (no booking, no purchases)
- Epoch 2 will add appointment booking tools
- Epoch 3 will add product search and cart tools

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.

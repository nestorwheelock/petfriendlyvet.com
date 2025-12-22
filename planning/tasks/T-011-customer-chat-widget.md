# T-011: Customer Chat Widget

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement customer-facing AI chat widget
**Related Story**: S-002
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/ai_assistant/, templates/chat/, static/js/
**Forbidden Paths**: apps/admin/

### Deliverables
- [ ] Floating chat button component
- [ ] Chat window with message history
- [ ] Message input with send button
- [ ] Streaming response display
- [ ] Typing indicators
- [ ] Quick action buttons
- [ ] Mobile-optimized layout
- [ ] Sound notifications (optional)

### Wireframe Reference
See: `planning/wireframes/09-ai-chat.txt`

### Implementation Details

#### HTMX + Alpine.js Chat Component
```html
<div x-data="chatWidget()" x-show="isOpen" class="chat-widget">
    <!-- Header -->
    <div class="chat-header">
        <span>Pet-Friendly AI</span>
        <button @click="isOpen = false">×</button>
    </div>

    <!-- Messages -->
    <div id="chat-messages" class="chat-messages">
        <template x-for="msg in messages">
            <div :class="msg.role === 'user' ? 'user-msg' : 'ai-msg'">
                <span x-text="msg.content"></span>
            </div>
        </template>
    </div>

    <!-- Input -->
    <form hx-post="/api/chat/" hx-trigger="submit" hx-swap="none">
        <input type="text" name="message" x-model="input">
        <button type="submit">Send</button>
    </form>
</div>
```

#### Streaming with SSE
```python
async def chat_stream(request):
    """Stream AI response via Server-Sent Events."""
    message = request.POST.get("message")

    async def event_generator():
        async for chunk in ai_service.stream_response(message):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingHttpResponse(
        event_generator(),
        content_type="text/event-stream"
    )
```

#### Quick Actions
Pre-defined quick action buttons:
- "What are your hours?"
- "Book appointment"
- "Check my pet's records"
- "Emergency help"

#### States
1. **Collapsed** - Floating button only
2. **Open** - Full chat window
3. **Loading** - Typing indicator
4. **Error** - Error message with retry

### Tailwind Classes
- Floating button: `fixed bottom-4 right-4 w-14 h-14 rounded-full bg-primary shadow-lg`
- Chat window: `fixed bottom-20 right-4 w-96 h-[500px] bg-white rounded-xl shadow-2xl`
- Messages: `overflow-y-auto p-4 space-y-3`
- User message: `bg-primary text-white rounded-lg p-3 ml-auto max-w-[80%]`
- AI message: `bg-gray-100 rounded-lg p-3 mr-auto max-w-[80%]`

### Test Cases
- [ ] Widget opens and closes
- [ ] Messages send and display
- [ ] Streaming response renders
- [ ] Quick actions work
- [ ] Mobile layout correct
- [ ] Error states handled
- [ ] History persists in session
- [ ] Accessibility (keyboard nav)

### Definition of Done
- [ ] Chat widget fully functional
- [ ] Streaming responses work
- [ ] Mobile-optimized
- [ ] Accessible
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-009: AI Service Layer
- T-010: Tool Calling Framework
- T-002: Base Templates

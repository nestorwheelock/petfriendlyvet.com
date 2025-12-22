"""Utility functions for AI assistant."""
from .models import Conversation


def get_conversation_context(conversation, max_messages=20):
    """Get conversation context as list of message dicts.

    Args:
        conversation: Conversation instance
        max_messages: Maximum messages to return (most recent)

    Returns:
        List of dicts with 'role' and 'content' keys
    """
    messages = conversation.messages.order_by('created_at')
    if max_messages:
        messages = messages[:max_messages]

    return [
        {'role': msg.role, 'content': msg.content}
        for msg in messages
    ]


def link_session_to_user(session_id, user):
    """Link anonymous session conversations to authenticated user.

    Args:
        session_id: The session ID to link
        user: The User instance to link to
    """
    Conversation.objects.filter(
        session_id=session_id,
        user__isnull=True
    ).update(user=user)


def export_conversation(conversation):
    """Export conversation data as dict.

    Args:
        conversation: Conversation instance

    Returns:
        Dict with session_id, language, messages, etc.
    """
    messages = []
    for msg in conversation.messages.order_by('created_at'):
        messages.append({
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat() if msg.created_at else None,
            'tool_calls': msg.tool_calls,
        })

    return {
        'session_id': conversation.session_id,
        'language': conversation.language,
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
        'messages': messages,
    }

"""AI Assistant models for chat and usage tracking."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AIUsage(models.Model):
    """Track AI API usage for cost monitoring and rate limiting."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('user')
    )
    session_id = models.CharField(
        _('session ID'),
        max_length=255,
        db_index=True
    )
    input_tokens = models.IntegerField(_('input tokens'))
    output_tokens = models.IntegerField(_('output tokens'))
    cost_usd = models.DecimalField(
        _('cost (USD)'),
        max_digits=10,
        decimal_places=6
    )
    model = models.CharField(_('model'), max_length=100)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('AI usage')
        verbose_name_plural = _('AI usage')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.model} - {self.input_tokens}+{self.output_tokens} tokens'


class Conversation(models.Model):
    """Chat conversation session."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name=_('user')
    )
    session_id = models.CharField(
        _('session ID'),
        max_length=255,
        unique=True,
        db_index=True
    )
    title = models.CharField(
        _('title'),
        max_length=200,
        blank=True,
        default=''
    )
    language = models.CharField(
        _('language'),
        max_length=5,
        default='es'
    )
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.session_id[:8]}... - {self.title or "Untitled"}'


class Message(models.Model):
    """Individual message in a conversation."""

    ROLE_CHOICES = [
        ('user', _('User')),
        ('assistant', _('Assistant')),
        ('system', _('System')),
        ('tool', _('Tool')),
    ]
    # Alias for backwards compatibility
    ROLES = ROLE_CHOICES

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversation')
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=ROLE_CHOICES
    )
    content = models.TextField(_('content'))
    tool_calls = models.JSONField(
        _('tool calls'),
        null=True,
        blank=True
    )
    tool_call_id = models.CharField(
        _('tool call ID'),
        max_length=100,
        blank=True,
        default=''
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}...'

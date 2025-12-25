"""Custom template tags for the loyalty app."""
from django import template

register = template.Library()


@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def abs_value(value):
    """Return absolute value."""
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return 0

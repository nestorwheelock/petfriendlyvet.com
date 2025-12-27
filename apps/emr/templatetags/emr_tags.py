"""EMR template tags and filters."""
from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key.

    Usage: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return []
    return dictionary.get(key, [])


@register.filter
def duration_clock(value):
    """Convert datetime to clock-style duration (H:MM or :MM).

    Examples:
        2 hours 30 minutes -> 2:30
        45 minutes -> :45
        1 hour 5 minutes -> 1:05
        3 hours -> 3:00
    """
    if not value:
        return ""

    now = timezone.now()
    delta = now - value

    total_minutes = int(delta.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}"
    else:
        return f":{minutes:02d}"

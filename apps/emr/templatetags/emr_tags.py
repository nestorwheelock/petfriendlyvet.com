"""EMR template tags and filters."""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key.

    Usage: {{ my_dict|get_item:key_var }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

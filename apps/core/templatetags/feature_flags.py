"""Template tags for feature flags.

Provides {% if_feature %} tag for conditional rendering based on feature flags.
"""
from django import template

from apps.core.feature_flags import is_enabled


register = template.Library()


class IfFeatureNode(template.Node):
    """Node for {% if_feature %} tag."""

    def __init__(self, feature_key, nodelist_true, nodelist_false=None):
        self.feature_key = feature_key
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false or template.NodeList()

    def render(self, context):
        # Resolve the feature key if it's a variable
        if hasattr(self.feature_key, 'resolve'):
            key = self.feature_key.resolve(context)
        else:
            key = self.feature_key

        if is_enabled(key):
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)


@register.tag('if_feature')
def do_if_feature(parser, token):
    """Template tag to conditionally render content based on feature flag.

    Usage:
        {% if_feature "feature.key" %}
            <button>Feature Enabled</button>
        {% endif_feature %}

        {% if_feature "feature.key" %}
            <button>Feature Enabled</button>
        {% else %}
            <span>Feature Disabled</span>
        {% endif_feature %}
    """
    bits = token.split_contents()

    if len(bits) != 2:
        raise template.TemplateSyntaxError(
            f"'{bits[0]}' tag requires exactly one argument (feature key)"
        )

    feature_key = bits[1]

    # Remove quotes if present
    if (feature_key.startswith('"') and feature_key.endswith('"')) or \
       (feature_key.startswith("'") and feature_key.endswith("'")):
        feature_key = feature_key[1:-1]
    else:
        # It's a variable, resolve it
        feature_key = parser.compile_filter(feature_key)

    nodelist_true = parser.parse(('else', 'endif_feature'))
    token = parser.next_token()

    if token.contents == 'else':
        nodelist_false = parser.parse(('endif_feature',))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()

    return IfFeatureNode(feature_key, nodelist_true, nodelist_false)


@register.simple_tag
def feature_enabled(key):
    """Simple tag that returns True/False for a feature flag.

    Usage:
        {% feature_enabled "feature.key" as is_enabled %}
        {% if is_enabled %}...{% endif %}
    """
    return is_enabled(key)

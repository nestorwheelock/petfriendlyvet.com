"""Context processors for the store app."""
from .models import Cart, StoreSettings


def cart(request):
    """Add cart to template context for all pages."""
    cart_obj = None
    cart_count = 0

    try:
        if request.user.is_authenticated:
            cart_obj = Cart.objects.filter(user=request.user).first()
        elif hasattr(request, 'session') and request.session.session_key:
            cart_obj = Cart.objects.filter(
                session_key=request.session.session_key,
                user__isnull=True
            ).first()

        if cart_obj:
            cart_count = cart_obj.item_count
    except Exception:
        # Silently fail if database isn't ready or other issues
        pass

    return {
        'cart': cart_obj,
        'cart_count': cart_count,
    }


def store_settings(request):
    """Add store settings to template context for all pages."""
    try:
        settings_obj = StoreSettings.get_instance()
    except Exception:
        settings_obj = None

    return {
        'store_settings': settings_obj,
    }

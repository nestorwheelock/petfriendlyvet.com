"""URL configuration for Pet-Friendly Vet project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from apps.core.views import health_check

# Non-i18n URLs
urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('i18n/', include('django.conf.urls.i18n')),
    # API endpoints (no i18n prefix)
    path('api/driver/', include('apps.delivery.api_urls')),
    path('api/delivery/', include('apps.delivery.customer_api_urls')),
    path('api/delivery/admin/', include('apps.delivery.admin_api_urls')),
    path('api/billing/', include('apps.billing.api_urls')),
    # Delivery driver dashboard (no i18n for mobile drivers)
    path('delivery/', include('apps.delivery.urls')),
]

# i18n URLs (language prefix)
urlpatterns += i18n_patterns(
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('pets/', include('apps.pets.urls')),
    path('appointments/', include('apps.appointments.urls')),
    path('store/', include('apps.store.urls')),
    path('pharmacy/', include('apps.pharmacy.urls')),
    path('billing/', include('apps.billing.urls')),
    path('chat/', include('apps.ai_assistant.urls')),
    path('crm/', include('apps.crm.urls')),
    path('practice/', include('apps.practice.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('services/', include('apps.services.urls')),
    path('travel/', include('apps.travel.urls')),
    path('loyalty/', include('apps.loyalty.urls')),
    path('emergency/', include('apps.emergency.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('referrals/', include('apps.referrals.urls')),
    prefix_default_language=False,
)

# Debug toolbar (development only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

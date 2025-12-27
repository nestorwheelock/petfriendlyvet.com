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
    # Public/customer-facing URLs
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('pets/', include('apps.pets.urls')),
    path('appointments/', include('apps.appointments.urls')),
    path('store/', include('apps.store.urls')),
    path('pharmacy/', include('apps.pharmacy.urls')),
    path('billing/', include('apps.billing.urls')),
    path('chat/', include('apps.ai_assistant.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('services/', include('apps.services.urls')),
    path('travel/', include('apps.travel.urls')),
    path('loyalty/', include('apps.loyalty.urls')),
    path('emergency/', include('apps.emergency.urls')),

    # =========================================================
    # Staff Portal URLs (Grouped by Section)
    # Accessed via /staff-{token}/section/module/
    # Middleware rewrites to /section/module/
    # =========================================================

    # Core Section (People, Organizations, Relationships, Pets)
    path('core/parties/', include('apps.parties.urls')),
    path('core/pets/', include('apps.pets.urls')),

    # Operations Section
    path('operations/practice/', include('apps.practice.urls')),
    path('operations/appointments/', include('apps.appointments.staff_urls')),
    path('operations/clinical/', include('apps.emr.urls')),
    path('operations/hr/', include('apps.hr.urls')),
    path('operations/inventory/', include('apps.inventory.urls')),
    path('operations/referrals/', include('apps.referrals.urls')),
    path('operations/delivery/', include('apps.delivery.admin_urls')),

    # Customers Section
    path('customers/crm/', include('apps.crm.urls')),
    path('customers/marketing/', include('apps.email_marketing.urls')),

    # Finance Section
    path('finance/accounting/', include('apps.accounting.urls')),
    path('finance/reports/', include('apps.reports.urls')),

    # Admin Section
    path('admin-tools/audit/', include('apps.audit.urls')),
    path('admin-tools/ai-chat/', include('apps.ai_assistant.urls')),

    # Superadmin (system administration)
    path('superadmin/', include('apps.superadmin.urls')),

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

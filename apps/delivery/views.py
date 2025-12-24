"""Views for the delivery app."""
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden

from .models import Delivery, DeliveryDriver


class DriverRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is an active driver."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        try:
            self.driver = request.user.delivery_driver
            if not self.driver.is_active:
                return HttpResponseForbidden("Driver account is inactive")
        except DeliveryDriver.DoesNotExist:
            return HttpResponseForbidden("User is not a driver")

        return super().dispatch(request, *args, **kwargs)


class DriverDashboardView(DriverRequiredMixin, View):
    """Driver mobile dashboard showing assigned deliveries."""

    def get(self, request):
        """Display driver's active deliveries."""
        deliveries = Delivery.objects.filter(
            driver=self.driver
        ).exclude(
            status__in=['delivered', 'returned']
        ).select_related(
            'order', 'zone', 'slot'
        ).order_by('scheduled_date', 'scheduled_time_start')

        context = {
            'driver': self.driver,
            'deliveries': deliveries,
        }
        return render(request, 'delivery/driver/dashboard.html', context)

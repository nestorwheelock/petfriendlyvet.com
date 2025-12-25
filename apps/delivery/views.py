"""Views for the delivery app."""
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404
from django.utils.translation import gettext as _

from .models import Delivery, DeliveryDriver


class DriverRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is an active driver."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        try:
            self.driver = request.user.delivery_driver
            if not self.driver.is_active:
                messages.error(request, _("Your driver account is inactive."))
                return redirect('delivery_admin:dashboard')
        except DeliveryDriver.DoesNotExist:
            # Non-drivers get redirected to admin dashboard if staff, home otherwise
            if request.user.is_staff:
                return redirect('delivery_admin:dashboard')
            messages.error(request, _("You don't have access to the driver dashboard."))
            return redirect('core:home')

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


class DeliveryTrackingView(LoginRequiredMixin, View):
    """Customer-facing delivery tracking page."""

    def get(self, request, delivery_number):
        """Display delivery tracking page."""
        delivery = get_object_or_404(
            Delivery.objects.select_related(
                'order', 'driver', 'zone', 'slot'
            ),
            delivery_number=delivery_number
        )

        # Ensure user owns this delivery
        if delivery.order.user != request.user:
            raise Http404("Delivery not found")

        # Get status history
        status_history = delivery.status_history.all().order_by('-created_at')

        # Define status steps for timeline
        status_steps = [
            ('pending', 'Pendiente', 'Pedido recibido'),
            ('assigned', 'Asignado', 'Conductor asignado'),
            ('picked_up', 'Recogido', 'Pedido recogido'),
            ('out_for_delivery', 'En camino', 'En ruta de entrega'),
            ('arrived', 'Llegó', 'Conductor llegó'),
            ('delivered', 'Entregado', 'Entrega completada'),
        ]

        # Determine which steps are complete
        status_order = [s[0] for s in status_steps]
        current_index = status_order.index(delivery.status) if delivery.status in status_order else -1

        timeline = []
        for i, (status, label, description) in enumerate(status_steps):
            timeline.append({
                'status': status,
                'label': label,
                'description': description,
                'is_complete': i <= current_index,
                'is_current': i == current_index,
            })

        context = {
            'delivery': delivery,
            'status_history': status_history,
            'timeline': timeline,
        }
        return render(request, 'delivery/tracking.html', context)

"""API views for delivery driver mobile app."""
import json
from decimal import Decimal

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Delivery, DeliveryDriver


class DriverRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is a driver."""

    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)

        try:
            self.driver = request.user.delivery_driver
            if not self.driver.is_active:
                return JsonResponse({'error': 'Driver account is inactive'}, status=403)
        except DeliveryDriver.DoesNotExist:
            return JsonResponse({'error': 'User is not a driver'}, status=403)

        return super().dispatch(request, *args, **kwargs)


@method_decorator(csrf_exempt, name='dispatch')
class DriverDeliveriesView(DriverRequiredMixin, View):
    """List driver's assigned deliveries."""

    def get(self, request):
        """Get list of deliveries assigned to the driver."""
        deliveries = Delivery.objects.filter(
            driver=self.driver
        ).exclude(
            status__in=['delivered', 'returned']
        ).select_related('order', 'zone', 'slot').order_by('scheduled_date', 'scheduled_time_start')

        data = {
            'deliveries': [
                {
                    'id': d.id,
                    'delivery_number': d.delivery_number,
                    'status': d.status,
                    'status_display': d.get_status_display(),
                    'address': d.address,
                    'latitude': str(d.latitude) if d.latitude else None,
                    'longitude': str(d.longitude) if d.longitude else None,
                    'scheduled_date': str(d.scheduled_date) if d.scheduled_date else None,
                    'scheduled_time_start': str(d.scheduled_time_start) if d.scheduled_time_start else None,
                    'scheduled_time_end': str(d.scheduled_time_end) if d.scheduled_time_end else None,
                    'notes': d.notes,
                    'order_number': d.order.order_number,
                    'zone': d.zone.name if d.zone else None,
                }
                for d in deliveries
            ]
        }
        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
class DriverDeliveryDetailView(DriverRequiredMixin, View):
    """Get details of a specific delivery."""

    def get(self, request, delivery_id):
        """Get delivery details."""
        try:
            delivery = Delivery.objects.select_related(
                'order', 'zone', 'slot'
            ).get(id=delivery_id, driver=self.driver)
        except Delivery.DoesNotExist:
            return JsonResponse({'error': 'Delivery not found'}, status=404)

        data = {
            'id': delivery.id,
            'delivery_number': delivery.delivery_number,
            'status': delivery.status,
            'status_display': delivery.get_status_display(),
            'address': delivery.address,
            'latitude': str(delivery.latitude) if delivery.latitude else None,
            'longitude': str(delivery.longitude) if delivery.longitude else None,
            'scheduled_date': str(delivery.scheduled_date) if delivery.scheduled_date else None,
            'scheduled_time_start': str(delivery.scheduled_time_start) if delivery.scheduled_time_start else None,
            'scheduled_time_end': str(delivery.scheduled_time_end) if delivery.scheduled_time_end else None,
            'notes': delivery.notes,
            'driver_notes': delivery.driver_notes,
            'order': {
                'order_number': delivery.order.order_number,
                'total': str(delivery.order.total),
                'customer_name': delivery.order.user.get_full_name() or delivery.order.user.username,
            },
            'zone': {
                'code': delivery.zone.code,
                'name': delivery.zone.name,
            } if delivery.zone else None,
            'status_history': [
                {
                    'from_status': h.from_status,
                    'to_status': h.to_status,
                    'created_at': h.created_at.isoformat(),
                }
                for h in delivery.status_history.all()
            ]
        }
        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
class DriverLocationUpdateView(DriverRequiredMixin, View):
    """Update driver's current location."""

    def post(self, request):
        """Update driver location with GPS coordinates."""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is None or longitude is None:
            return JsonResponse({'error': 'Coordinates required'}, status=400)

        self.driver.current_latitude = Decimal(str(latitude))
        self.driver.current_longitude = Decimal(str(longitude))
        self.driver.location_updated_at = timezone.now()
        self.driver.save(update_fields=['current_latitude', 'current_longitude', 'location_updated_at'])

        return JsonResponse({
            'success': True,
            'latitude': str(self.driver.current_latitude),
            'longitude': str(self.driver.current_longitude),
        })


@method_decorator(csrf_exempt, name='dispatch')
class DriverUpdateStatusView(DriverRequiredMixin, View):
    """Update delivery status."""

    def post(self, request, delivery_id):
        """Update delivery status with optional GPS coordinates."""
        try:
            delivery = Delivery.objects.get(id=delivery_id)
        except Delivery.DoesNotExist:
            return JsonResponse({'error': 'Delivery not found'}, status=404)

        # Check if delivery is assigned to this driver
        if delivery.driver != self.driver:
            return JsonResponse({'error': 'Not authorized to update this delivery'}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        new_status = data.get('status')
        if not new_status:
            return JsonResponse({'error': 'Status is required'}, status=400)

        # Get optional GPS coordinates
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude:
            latitude = Decimal(str(latitude))
        if longitude:
            longitude = Decimal(str(longitude))

        # Map status to appropriate method
        try:
            if new_status == 'picked_up':
                delivery.mark_picked_up(
                    changed_by=request.user,
                    latitude=latitude,
                    longitude=longitude
                )
            elif new_status == 'out_for_delivery':
                delivery.mark_out_for_delivery(
                    changed_by=request.user,
                    latitude=latitude,
                    longitude=longitude
                )
            elif new_status == 'arrived':
                delivery.mark_arrived(
                    changed_by=request.user,
                    latitude=latitude,
                    longitude=longitude
                )
            elif new_status == 'delivered':
                delivery.mark_delivered(
                    changed_by=request.user,
                    latitude=latitude,
                    longitude=longitude
                )
            elif new_status == 'failed':
                reason = data.get('reason', '')
                delivery.mark_failed(
                    reason=reason,
                    changed_by=request.user,
                    latitude=latitude,
                    longitude=longitude
                )
            else:
                return JsonResponse({'error': f'Invalid status: {new_status}'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

        return JsonResponse({
            'success': True,
            'delivery_number': delivery.delivery_number,
            'status': delivery.status,
            'status_display': delivery.get_status_display(),
        })

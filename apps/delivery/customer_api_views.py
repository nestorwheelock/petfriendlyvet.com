"""Customer-facing API views for delivery."""
from datetime import date

from django.http import JsonResponse
from django.views import View
from django.db.models import F

import json

from .models import Delivery, DeliverySlot, DeliveryZone, DeliveryRating


class AvailableSlotsView(View):
    """Get available delivery slots for a date."""

    def get(self, request):
        """Return available slots for given date and optional zone."""
        date_str = request.GET.get('date')
        zone_code = request.GET.get('zone')

        if not date_str:
            return JsonResponse({'error': 'date parameter is required'}, status=400)

        try:
            requested_date = date.fromisoformat(date_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        # Don't show past dates
        if requested_date < date.today():
            return JsonResponse({'slots': []})

        # Query available slots
        slots = DeliverySlot.objects.filter(
            date=requested_date,
            is_active=True,
            booked_count__lt=F('capacity')
        ).select_related('zone').order_by('start_time')

        # Filter by zone if specified
        if zone_code:
            slots = slots.filter(zone__code=zone_code)

        slots_data = [
            {
                'id': slot.id,
                'zone_code': slot.zone.code,
                'zone_name': slot.zone.name,
                'date': str(slot.date),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'time_display': f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}",
                'available_capacity': slot.available_capacity,
            }
            for slot in slots
        ]

        return JsonResponse({'slots': slots_data})


class AvailableDatesView(View):
    """Get dates that have available delivery slots."""

    def get(self, request):
        """Return dates with available slots in the next 14 days."""
        zone_code = request.GET.get('zone')
        today = date.today()

        # Get slots with available capacity
        slots = DeliverySlot.objects.filter(
            date__gte=today,
            is_active=True,
            booked_count__lt=F('capacity')
        )

        if zone_code:
            slots = slots.filter(zone__code=zone_code)

        # Get unique dates
        dates = slots.values_list('date', flat=True).distinct().order_by('date')

        return JsonResponse({
            'dates': [str(d) for d in dates]
        })


class DeliveryZonesView(View):
    """Get available delivery zones."""

    def get(self, request):
        """Return active delivery zones."""
        zones = DeliveryZone.objects.filter(is_active=True).order_by('name')

        zones_data = [
            {
                'code': zone.code,
                'name': zone.name,
                'fee': str(zone.delivery_fee) if zone.delivery_fee else None,
                'eta_min': zone.eta_minutes_min,
                'eta_max': zone.eta_minutes_max,
            }
            for zone in zones
        ]

        return JsonResponse({'zones': zones_data})


class DeliveryTrackingAPIView(View):
    """API to get delivery tracking status."""

    def get(self, request, delivery_number):
        """Return current delivery status and details."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)

        try:
            delivery = Delivery.objects.select_related(
                'driver', 'zone', 'slot'
            ).get(delivery_number=delivery_number)
        except Delivery.DoesNotExist:
            return JsonResponse({'error': 'Delivery not found'}, status=404)

        # Ensure user owns this delivery
        if delivery.order.user != request.user:
            return JsonResponse({'error': 'Delivery not found'}, status=404)

        # Build response data
        data = {
            'delivery_number': delivery.delivery_number,
            'status': delivery.status,
            'status_display': delivery.get_status_display(),
            'address': delivery.address,
            'scheduled_date': str(delivery.scheduled_date) if delivery.scheduled_date else None,
            'scheduled_time': None,
            'driver': None,
            'driver_location': None,
            'timestamps': {
                'assigned_at': delivery.assigned_at.isoformat() if delivery.assigned_at else None,
                'picked_up_at': delivery.picked_up_at.isoformat() if delivery.picked_up_at else None,
                'out_for_delivery_at': delivery.out_for_delivery_at.isoformat() if delivery.out_for_delivery_at else None,
                'arrived_at': delivery.arrived_at.isoformat() if delivery.arrived_at else None,
                'delivered_at': delivery.delivered_at.isoformat() if delivery.delivered_at else None,
            }
        }

        # Add scheduled time
        if delivery.scheduled_time_start and delivery.scheduled_time_end:
            data['scheduled_time'] = f"{delivery.scheduled_time_start.strftime('%H:%M')} - {delivery.scheduled_time_end.strftime('%H:%M')}"

        # Add driver info if assigned
        if delivery.driver:
            data['driver'] = {
                'name': delivery.driver.user.get_full_name() or delivery.driver.user.username,
                'phone': delivery.driver.phone,
            }
            # Add driver location if available and out for delivery
            if delivery.status in ['out_for_delivery', 'arrived'] and delivery.driver.current_latitude:
                data['driver_location'] = {
                    'latitude': float(delivery.driver.current_latitude),
                    'longitude': float(delivery.driver.current_longitude),
                    'updated_at': delivery.driver.location_updated_at.isoformat() if delivery.driver.location_updated_at else None,
                }

        return JsonResponse(data)


class DeliveryRatingAPIView(View):
    """API to submit and get delivery ratings."""

    def get(self, request, delivery_number):
        """Get existing rating for a delivery."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)

        try:
            delivery = Delivery.objects.select_related('rating').get(
                delivery_number=delivery_number
            )
        except Delivery.DoesNotExist:
            return JsonResponse({'error': 'Delivery not found'}, status=404)

        # Ensure user owns this delivery
        if delivery.order.user != request.user:
            return JsonResponse({'error': 'Delivery not found'}, status=404)

        # Check if rating exists
        try:
            rating = delivery.rating
            return JsonResponse({
                'rating': rating.rating,
                'comment': rating.comment,
                'created_at': rating.created_at.isoformat(),
            })
        except DeliveryRating.DoesNotExist:
            return JsonResponse({'rating': None})

    def post(self, request, delivery_number):
        """Submit a rating for a delivery."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)

        try:
            delivery = Delivery.objects.get(delivery_number=delivery_number)
        except Delivery.DoesNotExist:
            return JsonResponse({'error': 'Delivery not found'}, status=404)

        # Ensure user owns this delivery
        if delivery.order.user != request.user:
            return JsonResponse({'error': 'Delivery not found'}, status=404)

        # Check if delivery is completed
        if delivery.status != 'delivered':
            return JsonResponse({'error': 'Delivery not yet delivered'}, status=400)

        # Check if already rated
        if hasattr(delivery, 'rating'):
            try:
                _ = delivery.rating
                return JsonResponse({'error': 'Delivery already rated'}, status=400)
            except DeliveryRating.DoesNotExist:
                pass

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        rating_value = data.get('rating')
        comment = data.get('comment', '')

        # Validate rating
        if rating_value is None:
            return JsonResponse({'error': 'Rating is required'}, status=400)

        try:
            rating_value = int(rating_value)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Rating must be a number'}, status=400)

        if rating_value < 1 or rating_value > 5:
            return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)

        # Create rating
        DeliveryRating.objects.create(
            delivery=delivery,
            rating=rating_value,
            comment=comment
        )

        return JsonResponse({
            'success': True,
            'rating': rating_value,
            'comment': comment,
        })

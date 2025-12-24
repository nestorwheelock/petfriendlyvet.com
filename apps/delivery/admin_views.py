"""Admin views for delivery management dashboard."""
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Avg
from django.utils import timezone

from .models import Delivery, DeliveryDriver, DeliveryZone, DeliverySlot, DeliveryRating
from .services import DeliveryPaymentService


class StaffRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is staff."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.is_staff:
            return HttpResponseForbidden("Staff access required")

        return super().dispatch(request, *args, **kwargs)


class AdminDashboardView(StaffRequiredMixin, View):
    """Admin dashboard for delivery operations."""

    def get(self, request):
        """Display delivery operations dashboard."""
        today = date.today()

        # Get today's deliveries
        deliveries = Delivery.objects.filter(
            scheduled_date=today
        ).select_related(
            'order', 'driver', 'zone', 'slot'
        ).order_by('scheduled_time_start', 'status')

        # Calculate statistics
        stats = {
            'total': deliveries.count(),
            'pending': deliveries.filter(status='pending').count(),
            'assigned': deliveries.filter(status='assigned').count(),
            'in_progress': deliveries.filter(
                status__in=['picked_up', 'out_for_delivery', 'arrived']
            ).count(),
            'delivered': deliveries.filter(status='delivered').count(),
            'failed': deliveries.filter(status='failed').count(),
        }

        # Get available drivers
        drivers = DeliveryDriver.objects.filter(
            is_active=True
        ).select_related('user')

        # Get zones
        zones = DeliveryZone.objects.filter(is_active=True)

        context = {
            'deliveries': deliveries,
            'stats': stats,
            'drivers': drivers,
            'zones': zones,
            'today': today,
        }
        return render(request, 'delivery/admin/dashboard.html', context)


class AdminDeliveriesAPIView(StaffRequiredMixin, View):
    """API to get deliveries for map display."""

    def get(self, request):
        """Return deliveries with location data."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)

        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        today = date.today()
        date_filter = request.GET.get('date', str(today))

        deliveries = Delivery.objects.filter(
            scheduled_date=date_filter
        ).select_related('order', 'driver', 'zone')

        # Optional status filter
        status_filter = request.GET.get('status')
        if status_filter:
            deliveries = deliveries.filter(status=status_filter)

        deliveries_data = []
        for d in deliveries:
            delivery_data = {
                'id': d.id,
                'delivery_number': d.delivery_number,
                'status': d.status,
                'status_display': d.get_status_display(),
                'address': d.address,
                'latitude': float(d.latitude) if d.latitude else None,
                'longitude': float(d.longitude) if d.longitude else None,
                'scheduled_time': None,
                'order_number': d.order.order_number,
                'zone': d.zone.name if d.zone else None,
                'driver': None,
            }

            if d.scheduled_time_start and d.scheduled_time_end:
                delivery_data['scheduled_time'] = f"{d.scheduled_time_start.strftime('%H:%M')} - {d.scheduled_time_end.strftime('%H:%M')}"

            if d.driver:
                delivery_data['driver'] = {
                    'id': d.driver.id,
                    'name': d.driver.user.get_full_name() or d.driver.user.username,
                }

            deliveries_data.append(delivery_data)

        return JsonResponse({'deliveries': deliveries_data})


class AdminDriversAPIView(StaffRequiredMixin, View):
    """API to get driver locations for map display."""

    def get(self, request):
        """Return active drivers with their locations."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)

        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        drivers = DeliveryDriver.objects.filter(
            is_active=True
        ).select_related('user')

        drivers_data = []
        for driver in drivers:
            driver_data = {
                'id': driver.id,
                'name': driver.user.get_full_name() or driver.user.username,
                'is_available': driver.is_available,
                'latitude': float(driver.current_latitude) if driver.current_latitude else None,
                'longitude': float(driver.current_longitude) if driver.current_longitude else None,
                'location_updated_at': driver.location_updated_at.isoformat() if driver.location_updated_at else None,
                'active_deliveries': driver.deliveries.exclude(
                    status__in=['delivered', 'failed', 'returned']
                ).count(),
            }
            drivers_data.append(driver_data)

        return JsonResponse({'drivers': drivers_data})


class AdminAssignDriverView(StaffRequiredMixin, View):
    """API to assign a driver to a delivery."""

    def post(self, request, delivery_id):
        """Assign driver to delivery."""
        import json

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)

        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            delivery = Delivery.objects.get(id=delivery_id)
        except Delivery.DoesNotExist:
            return JsonResponse({'error': 'Delivery not found'}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        driver_id = data.get('driver_id')
        if not driver_id:
            return JsonResponse({'error': 'driver_id is required'}, status=400)

        try:
            driver = DeliveryDriver.objects.get(id=driver_id, is_active=True)
        except DeliveryDriver.DoesNotExist:
            return JsonResponse({'error': 'Driver not found or inactive'}, status=404)

        # Assign driver and update status
        delivery.driver = driver
        delivery.assigned_at = timezone.now()
        if delivery.status == 'pending':
            delivery.status = 'assigned'
        delivery.save()

        return JsonResponse({
            'success': True,
            'delivery_number': delivery.delivery_number,
            'driver': {
                'id': driver.id,
                'name': driver.user.get_full_name() or driver.user.username,
            }
        })


class ReportsView(StaffRequiredMixin, View):
    """Delivery reports page."""

    def get(self, request):
        """Display delivery reports page."""
        today = date.today()

        # Default to last 30 days
        start_date = today - timedelta(days=30)
        end_date = today

        context = {
            'today': today,
            'start_date': start_date,
            'end_date': end_date,
            'drivers': DeliveryDriver.objects.filter(is_active=True).select_related('user'),
            'zones': DeliveryZone.objects.filter(is_active=True),
        }
        return render(request, 'delivery/admin/reports.html', context)


class AdminReportsAPIView(StaffRequiredMixin, View):
    """API for delivery reports and analytics."""

    def get(self, request):
        """Return delivery statistics and analytics."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)

        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        # Parse date range
        today = date.today()
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                start_date = today - timedelta(days=30)
        else:
            start_date = today - timedelta(days=30)

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = today
        else:
            end_date = today

        # Filter deliveries
        deliveries = Delivery.objects.filter(
            scheduled_date__gte=start_date,
            scheduled_date__lte=end_date
        )

        # Basic stats
        total = deliveries.count()
        delivered = deliveries.filter(status='delivered').count()
        failed = deliveries.filter(status='failed').count()
        pending = deliveries.filter(status='pending').count()

        # On-time rate calculation
        on_time_count = 0
        late_count = 0
        for d in deliveries.filter(status='delivered'):
            if d.delivered_at and d.scheduled_time_end:
                scheduled_end = datetime.combine(d.scheduled_date, d.scheduled_time_end)
                if d.delivered_at.replace(tzinfo=None) <= scheduled_end:
                    on_time_count += 1
                else:
                    late_count += 1

        on_time_rate = (on_time_count / (on_time_count + late_count) * 100) if (on_time_count + late_count) > 0 else 0

        # Average rating
        ratings = DeliveryRating.objects.filter(
            delivery__scheduled_date__gte=start_date,
            delivery__scheduled_date__lte=end_date
        )
        avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0

        stats = {
            'total': total,
            'delivered': delivered,
            'failed': failed,
            'pending': pending,
            'delivery_rate': (delivered / total * 100) if total > 0 else 0,
            'failure_rate': (failed / total * 100) if total > 0 else 0,
            'on_time_rate': round(on_time_rate, 1),
            'average_rating': round(float(avg_rating), 2) if avg_rating else 0,
        }

        # Driver performance
        driver_performance = []
        drivers = DeliveryDriver.objects.filter(is_active=True).select_related('user')

        for driver in drivers:
            driver_deliveries = deliveries.filter(driver=driver)
            driver_delivered = driver_deliveries.filter(status='delivered').count()
            driver_failed = driver_deliveries.filter(status='failed').count()
            driver_total = driver_deliveries.count()

            # Get driver's average rating
            driver_ratings = DeliveryRating.objects.filter(
                delivery__driver=driver,
                delivery__scheduled_date__gte=start_date,
                delivery__scheduled_date__lte=end_date
            )
            driver_avg_rating = driver_ratings.aggregate(avg=Avg('rating'))['avg']

            if driver_total > 0:
                driver_performance.append({
                    'id': driver.id,
                    'name': driver.user.get_full_name() or driver.user.username,
                    'total_deliveries': driver_total,
                    'delivered': driver_delivered,
                    'failed': driver_failed,
                    'success_rate': round(driver_delivered / driver_total * 100, 1) if driver_total > 0 else 0,
                    'average_rating': round(float(driver_avg_rating), 2) if driver_avg_rating else 0,
                })

        # Sort by total deliveries descending
        driver_performance.sort(key=lambda x: x['total_deliveries'], reverse=True)

        # Zone stats
        zone_stats = []
        zones = DeliveryZone.objects.filter(is_active=True)

        for zone in zones:
            zone_deliveries = deliveries.filter(zone=zone)
            zone_total = zone_deliveries.count()
            zone_delivered = zone_deliveries.filter(status='delivered').count()

            if zone_total > 0:
                zone_stats.append({
                    'code': zone.code,
                    'name': zone.name,
                    'total': zone_total,
                    'delivered': zone_delivered,
                    'delivery_rate': round(zone_delivered / zone_total * 100, 1) if zone_total > 0 else 0,
                })

        # Sort by total deliveries descending
        zone_stats.sort(key=lambda x: x['total'], reverse=True)

        return JsonResponse({
            'stats': stats,
            'driver_performance': driver_performance,
            'zone_stats': zone_stats,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            }
        })


class AdminDriverReportAPIView(StaffRequiredMixin, View):
    """API for individual driver reports."""

    def get(self, request, driver_id):
        """Return detailed stats for a specific driver."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)

        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            driver = DeliveryDriver.objects.select_related('user').get(id=driver_id)
        except DeliveryDriver.DoesNotExist:
            return JsonResponse({'error': 'Driver not found'}, status=404)

        # Parse date range
        today = date.today()
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                start_date = today - timedelta(days=30)
        else:
            start_date = today - timedelta(days=30)

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                end_date = today
        else:
            end_date = today

        # Get driver deliveries
        deliveries = Delivery.objects.filter(
            driver=driver,
            scheduled_date__gte=start_date,
            scheduled_date__lte=end_date
        )

        total = deliveries.count()
        delivered = deliveries.filter(status='delivered').count()
        failed = deliveries.filter(status='failed').count()

        # Ratings
        ratings = DeliveryRating.objects.filter(
            delivery__driver=driver,
            delivery__scheduled_date__gte=start_date,
            delivery__scheduled_date__lte=end_date
        )
        avg_rating = ratings.aggregate(avg=Avg('rating'))['avg']

        # Daily breakdown
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            day_deliveries = deliveries.filter(scheduled_date=current_date)
            day_delivered = day_deliveries.filter(status='delivered').count()
            day_total = day_deliveries.count()
            if day_total > 0:
                daily_stats.append({
                    'date': current_date.isoformat(),
                    'total': day_total,
                    'delivered': day_delivered,
                })
            current_date += timedelta(days=1)

        return JsonResponse({
            'driver': {
                'id': driver.id,
                'name': driver.user.get_full_name() or driver.user.username,
                'driver_type': driver.driver_type,
                'vehicle_type': driver.vehicle_type,
                'is_available': driver.is_available,
            },
            'stats': {
                'total': total,
                'delivered': delivered,
                'failed': failed,
                'success_rate': round(delivered / total * 100, 1) if total > 0 else 0,
                'average_rating': round(float(avg_rating), 2) if avg_rating else 0,
            },
            'daily_stats': daily_stats,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            }
        })


class ZonesView(StaffRequiredMixin, View):
    """Zone management page."""

    def get(self, request):
        """Display zone management page."""
        zones = DeliveryZone.objects.all().order_by('code')
        context = {
            'zones': zones,
        }
        return render(request, 'delivery/admin/zones.html', context)


class SlotsView(StaffRequiredMixin, View):
    """Slot management page."""

    def get(self, request):
        """Display slot management page."""
        today = date.today()
        zones = DeliveryZone.objects.filter(is_active=True).order_by('code')
        slots = DeliverySlot.objects.filter(
            date__gte=today
        ).select_related('zone').order_by('date', 'start_time')

        context = {
            'zones': zones,
            'slots': slots,
            'today': today,
        }
        return render(request, 'delivery/admin/slots.html', context)


class AdminZonesAPIView(StaffRequiredMixin, View):
    """API for zone CRUD operations."""

    def get(self, request):
        """List all zones."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        zones = DeliveryZone.objects.all().order_by('code')
        zones_data = [{
            'id': z.id,
            'code': z.code,
            'name': z.name,
            'name_es': z.name_es,
            'delivery_fee': str(z.delivery_fee),
            'estimated_time_minutes': z.estimated_time_minutes,
            'is_active': z.is_active,
        } for z in zones]

        return JsonResponse({'zones': zones_data})

    def post(self, request):
        """Create a new zone."""
        import json

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        code = data.get('code')
        name = data.get('name')

        if not code or not name:
            return JsonResponse({'error': 'code and name are required'}, status=400)

        if DeliveryZone.objects.filter(code=code).exists():
            return JsonResponse({'error': 'Zone code already exists'}, status=400)

        zone = DeliveryZone.objects.create(
            code=code,
            name=name,
            name_es=data.get('name_es', ''),
            delivery_fee=Decimal(data.get('delivery_fee', '50.00')),
            estimated_time_minutes=data.get('estimated_time_minutes', 45),
            is_active=data.get('is_active', True)
        )

        return JsonResponse({
            'zone': {
                'id': zone.id,
                'code': zone.code,
                'name': zone.name,
                'delivery_fee': str(zone.delivery_fee),
                'estimated_time_minutes': zone.estimated_time_minutes,
                'is_active': zone.is_active,
            }
        }, status=201)


class AdminZoneDetailAPIView(StaffRequiredMixin, View):
    """API for single zone operations."""

    def put(self, request, zone_id):
        """Update a zone."""
        import json

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            zone = DeliveryZone.objects.get(id=zone_id)
        except DeliveryZone.DoesNotExist:
            return JsonResponse({'error': 'Zone not found'}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if 'code' in data:
            zone.code = data['code']
        if 'name' in data:
            zone.name = data['name']
        if 'name_es' in data:
            zone.name_es = data['name_es']
        if 'delivery_fee' in data:
            zone.delivery_fee = Decimal(data['delivery_fee'])
        if 'estimated_time_minutes' in data:
            zone.estimated_time_minutes = data['estimated_time_minutes']
        if 'is_active' in data:
            zone.is_active = data['is_active']

        zone.save()

        return JsonResponse({
            'zone': {
                'id': zone.id,
                'code': zone.code,
                'name': zone.name,
                'delivery_fee': str(zone.delivery_fee),
                'estimated_time_minutes': zone.estimated_time_minutes,
                'is_active': zone.is_active,
            }
        })

    def delete(self, request, zone_id):
        """Deactivate a zone (soft delete)."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            zone = DeliveryZone.objects.get(id=zone_id)
        except DeliveryZone.DoesNotExist:
            return JsonResponse({'error': 'Zone not found'}, status=404)

        zone.is_active = False
        zone.save()

        return JsonResponse({'success': True, 'message': 'Zone deactivated'})


class AdminSlotsAPIView(StaffRequiredMixin, View):
    """API for slot CRUD operations."""

    def get(self, request):
        """List slots."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        today = date.today()
        zone_id = request.GET.get('zone_id')
        date_filter = request.GET.get('date')

        slots = DeliverySlot.objects.filter(
            date__gte=today
        ).select_related('zone').order_by('date', 'start_time')

        if zone_id:
            slots = slots.filter(zone_id=zone_id)
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                slots = slots.filter(date=filter_date)
            except ValueError:
                pass

        slots_data = [{
            'id': s.id,
            'zone_id': s.zone_id,
            'zone_code': s.zone.code,
            'date': s.date.isoformat(),
            'start_time': s.start_time.strftime('%H:%M'),
            'end_time': s.end_time.strftime('%H:%M'),
            'capacity': s.capacity,
            'booked_count': s.booked_count,
            'available_capacity': s.available_capacity,
            'is_active': s.is_active,
        } for s in slots]

        return JsonResponse({'slots': slots_data})

    def post(self, request):
        """Create a new slot."""
        import json

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        zone_id = data.get('zone_id')
        slot_date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        capacity = data.get('capacity', 5)

        if not all([zone_id, slot_date, start_time, end_time]):
            return JsonResponse({
                'error': 'zone_id, date, start_time, and end_time are required'
            }, status=400)

        try:
            zone = DeliveryZone.objects.get(id=zone_id)
        except DeliveryZone.DoesNotExist:
            return JsonResponse({'error': 'Zone not found'}, status=404)

        try:
            slot_date = datetime.strptime(slot_date, '%Y-%m-%d').date()
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            return JsonResponse({'error': 'Invalid date or time format'}, status=400)

        slot = DeliverySlot.objects.create(
            zone=zone,
            date=slot_date,
            start_time=start_time_obj,
            end_time=end_time_obj,
            capacity=capacity
        )

        return JsonResponse({
            'slot': {
                'id': slot.id,
                'zone_id': slot.zone_id,
                'date': slot.date.isoformat(),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'capacity': slot.capacity,
                'is_active': slot.is_active,
            }
        }, status=201)


class AdminSlotDetailAPIView(StaffRequiredMixin, View):
    """API for single slot operations."""

    def put(self, request, slot_id):
        """Update a slot."""
        import json

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            slot = DeliverySlot.objects.get(id=slot_id)
        except DeliverySlot.DoesNotExist:
            return JsonResponse({'error': 'Slot not found'}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if 'capacity' in data:
            slot.capacity = data['capacity']
        if 'is_active' in data:
            slot.is_active = data['is_active']
        if 'start_time' in data:
            slot.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            slot.end_time = datetime.strptime(data['end_time'], '%H:%M').time()

        slot.save()

        return JsonResponse({
            'slot': {
                'id': slot.id,
                'zone_id': slot.zone_id,
                'date': slot.date.isoformat(),
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'capacity': slot.capacity,
                'is_active': slot.is_active,
            }
        })

    def delete(self, request, slot_id):
        """Deactivate a slot (soft delete)."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            slot = DeliverySlot.objects.get(id=slot_id)
        except DeliverySlot.DoesNotExist:
            return JsonResponse({'error': 'Slot not found'}, status=404)

        slot.is_active = False
        slot.save()

        return JsonResponse({'success': True, 'message': 'Slot deactivated'})


class AdminSlotsBulkCreateAPIView(StaffRequiredMixin, View):
    """API for bulk creating slots."""

    def post(self, request):
        """Create slots for multiple days."""
        import json

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        zone_id = data.get('zone_id')
        start_date_str = data.get('start_date')
        days = data.get('days', 7)
        slot_templates = data.get('slots', [])

        if not all([zone_id, start_date_str, slot_templates]):
            return JsonResponse({
                'error': 'zone_id, start_date, and slots are required'
            }, status=400)

        try:
            zone = DeliveryZone.objects.get(id=zone_id)
        except DeliveryZone.DoesNotExist:
            return JsonResponse({'error': 'Zone not found'}, status=404)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)

        created_count = 0
        current_date = start_date

        for _ in range(days):
            for slot_template in slot_templates:
                try:
                    start_time = datetime.strptime(slot_template['start_time'], '%H:%M').time()
                    end_time = datetime.strptime(slot_template['end_time'], '%H:%M').time()
                    capacity = slot_template.get('capacity', 5)

                    # Check if slot already exists
                    if not DeliverySlot.objects.filter(
                        zone=zone,
                        date=current_date,
                        start_time=start_time
                    ).exists():
                        DeliverySlot.objects.create(
                            zone=zone,
                            date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            capacity=capacity
                        )
                        created_count += 1
                except (ValueError, KeyError):
                    continue

            current_date += timedelta(days=1)

        return JsonResponse({
            'success': True,
            'created_count': created_count
        }, status=201)


class ContractorsView(StaffRequiredMixin, View):
    """Contractor management page."""

    def get(self, request):
        """Display contractor management page."""
        contractors = DeliveryDriver.objects.filter(
            driver_type='contractor'
        ).select_related('user').order_by('-created_at')

        zones = DeliveryZone.objects.filter(is_active=True).order_by('code')

        context = {
            'contractors': contractors,
            'zones': zones,
        }
        return render(request, 'delivery/admin/contractors.html', context)


class AdminContractorsAPIView(StaffRequiredMixin, View):
    """API for contractor CRUD operations."""

    def get(self, request):
        """List all contractors."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        contractors = DeliveryDriver.objects.filter(
            driver_type='contractor'
        ).select_related('user').prefetch_related('zones')

        contractors_data = []
        for c in contractors:
            contractors_data.append({
                'id': c.id,
                'name': c.user.get_full_name() or c.user.username,
                'email': c.user.email,
                'phone': c.phone,
                'driver_type': c.driver_type,
                'rfc': c.rfc,
                'curp': c.curp,
                'vehicle_type': c.vehicle_type,
                'rate_per_delivery': str(c.rate_per_delivery) if c.rate_per_delivery else None,
                'rate_per_km': str(c.rate_per_km) if c.rate_per_km else None,
                'contract_signed': c.contract_signed,
                'onboarding_status': c.onboarding_status,
                'is_active': c.is_active,
                'is_available': c.is_available,
                'zones': [{'id': z.id, 'code': z.code} for z in c.zones.all()],
            })

        return JsonResponse({'contractors': contractors_data})

    def post(self, request):
        """Create a new contractor."""
        import json
        from django.contrib.auth import get_user_model

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        user_id = data.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'user_id is required'}, status=400)

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        # Check if user already has a driver profile
        if hasattr(user, 'delivery_driver'):
            return JsonResponse({'error': 'User already has a driver profile'}, status=400)

        contractor = DeliveryDriver.objects.create(
            user=user,
            driver_type='contractor',
            phone=data.get('phone', ''),
            rfc=data.get('rfc', ''),
            curp=data.get('curp', ''),
            vehicle_type=data.get('vehicle_type', 'motorcycle'),
            rate_per_delivery=Decimal(data.get('rate_per_delivery', '0')) if data.get('rate_per_delivery') else None,
            rate_per_km=Decimal(data.get('rate_per_km', '0')) if data.get('rate_per_km') else None,
            onboarding_status='pending'
        )

        # Add zones
        zone_ids = data.get('zone_ids', [])
        if zone_ids:
            zones = DeliveryZone.objects.filter(id__in=zone_ids)
            contractor.zones.set(zones)

        return JsonResponse({
            'contractor': {
                'id': contractor.id,
                'name': contractor.user.get_full_name() or contractor.user.username,
                'driver_type': contractor.driver_type,
                'onboarding_status': contractor.onboarding_status,
            }
        }, status=201)


class AdminContractorDetailAPIView(StaffRequiredMixin, View):
    """API for single contractor operations."""

    def get(self, request, contractor_id):
        """Get contractor details."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            contractor = DeliveryDriver.objects.select_related('user').prefetch_related('zones').get(
                id=contractor_id,
                driver_type='contractor'
            )
        except DeliveryDriver.DoesNotExist:
            return JsonResponse({'error': 'Contractor not found'}, status=404)

        return JsonResponse({
            'contractor': {
                'id': contractor.id,
                'name': contractor.user.get_full_name() or contractor.user.username,
                'email': contractor.user.email,
                'phone': contractor.phone,
                'driver_type': contractor.driver_type,
                'rfc': contractor.rfc,
                'curp': contractor.curp,
                'vehicle_type': contractor.vehicle_type,
                'rate_per_delivery': str(contractor.rate_per_delivery) if contractor.rate_per_delivery else None,
                'rate_per_km': str(contractor.rate_per_km) if contractor.rate_per_km else None,
                'contract_signed': contractor.contract_signed,
                'onboarding_status': contractor.onboarding_status,
                'onboarding_notes': contractor.onboarding_notes,
                'is_active': contractor.is_active,
                'is_available': contractor.is_available,
                'zones': [{'id': z.id, 'code': z.code, 'name': z.name} for z in contractor.zones.all()],
            }
        })

    def put(self, request, contractor_id):
        """Update a contractor."""
        import json

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            contractor = DeliveryDriver.objects.get(id=contractor_id, driver_type='contractor')
        except DeliveryDriver.DoesNotExist:
            return JsonResponse({'error': 'Contractor not found'}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if 'phone' in data:
            contractor.phone = data['phone']
        if 'rfc' in data:
            contractor.rfc = data['rfc']
        if 'curp' in data:
            contractor.curp = data['curp']
        if 'vehicle_type' in data:
            contractor.vehicle_type = data['vehicle_type']
        if 'rate_per_delivery' in data:
            contractor.rate_per_delivery = Decimal(data['rate_per_delivery']) if data['rate_per_delivery'] else None
        if 'rate_per_km' in data:
            contractor.rate_per_km = Decimal(data['rate_per_km']) if data['rate_per_km'] else None
        if 'contract_signed' in data:
            contractor.contract_signed = data['contract_signed']
        if 'onboarding_status' in data:
            contractor.onboarding_status = data['onboarding_status']
        if 'onboarding_notes' in data:
            contractor.onboarding_notes = data['onboarding_notes']
        if 'is_active' in data:
            contractor.is_active = data['is_active']

        contractor.save()

        if 'zone_ids' in data:
            zones = DeliveryZone.objects.filter(id__in=data['zone_ids'])
            contractor.zones.set(zones)

        return JsonResponse({
            'contractor': {
                'id': contractor.id,
                'name': contractor.user.get_full_name() or contractor.user.username,
                'onboarding_status': contractor.onboarding_status,
            }
        })


class ValidateRFCAPIView(StaffRequiredMixin, View):
    """API to validate Mexican RFC format."""

    def post(self, request):
        """Validate RFC format."""
        import json
        import re

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        rfc = data.get('rfc', '').upper().strip()

        # RFC pattern:
        # Persona moral: 3 letters + 6 digits + 3 alphanumeric (12 chars)
        # Persona fisica: 4 letters + 6 digits + 3 alphanumeric (13 chars)
        pattern_moral = r'^[A-Z&Ñ]{3}[0-9]{6}[A-Z0-9]{3}$'
        pattern_fisica = r'^[A-Z&Ñ]{4}[0-9]{6}[A-Z0-9]{3}$'

        is_valid = bool(re.match(pattern_moral, rfc) or re.match(pattern_fisica, rfc))

        return JsonResponse({
            'valid': is_valid,
            'rfc': rfc,
            'message': 'RFC valido' if is_valid else 'Formato de RFC invalido'
        })


class ValidateCURPAPIView(StaffRequiredMixin, View):
    """API to validate Mexican CURP format."""

    def post(self, request):
        """Validate CURP format."""
        import json
        import re

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        curp = data.get('curp', '').upper().strip()

        # CURP pattern: 18 characters
        # 4 letters + 6 digits + 1 letter (sex) + 2 letters (state) + 3 consonants + 2 alphanumeric
        pattern = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{2}[A-Z]{3}[A-Z0-9]{2}$'

        is_valid = bool(re.match(pattern, curp))

        return JsonResponse({
            'valid': is_valid,
            'curp': curp,
            'message': 'CURP valido' if is_valid else 'Formato de CURP invalido'
        })


class ContractorPaymentsAPIView(StaffRequiredMixin, View):
    """API for contractor payment summary."""

    def get(self, request):
        """Get payment summary for all contractors."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        # Get date range from query params
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            # Default to last 30 days
            start_date = date.today() - timedelta(days=30)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = date.today()

        # Get all contractors
        contractors = DeliveryDriver.objects.filter(driver_type='contractor')

        contractor_data = []
        total_earnings = Decimal('0.00')
        total_deliveries = 0

        for contractor in contractors:
            earnings = DeliveryPaymentService.calculate_driver_earnings(
                contractor, start_date, end_date
            )

            contractor_data.append({
                'id': contractor.id,
                'name': contractor.user.get_full_name() or contractor.user.username,
                'rfc': contractor.rfc,
                'curp': contractor.curp,
                'rate_per_delivery': str(contractor.rate_per_delivery) if contractor.rate_per_delivery else None,
                'rate_per_km': str(contractor.rate_per_km) if contractor.rate_per_km else None,
                'total_deliveries': earnings['total_deliveries'],
                'total_flat_rate': str(earnings['total_flat_rate']),
                'total_distance_payment': str(earnings['total_distance_payment']),
                'total_earnings': str(earnings['total_earnings']),
            })

            total_earnings += earnings['total_earnings']
            total_deliveries += earnings['total_deliveries']

        return JsonResponse({
            'contractors': contractor_data,
            'totals': {
                'total_contractors': len(contractor_data),
                'total_deliveries': total_deliveries,
                'total_earnings': str(total_earnings),
            },
            'date_range': {
                'start_date': str(start_date),
                'end_date': str(end_date),
            }
        })


class ContractorPaymentDetailAPIView(StaffRequiredMixin, View):
    """API for individual contractor payment details."""

    def get(self, request, contractor_id):
        """Get detailed payment report for a contractor."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=403)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Staff access required'}, status=403)

        try:
            contractor = DeliveryDriver.objects.get(id=contractor_id)
        except DeliveryDriver.DoesNotExist:
            return JsonResponse({'error': 'Contractor not found'}, status=404)

        # Get date range from query params
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = date.today() - timedelta(days=30)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = date.today()

        # Get delivered deliveries for this contractor
        deliveries = Delivery.objects.filter(
            driver=contractor,
            status='delivered',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('order', 'zone').order_by('-delivered_at')

        delivery_data = []
        total_flat_rate = Decimal('0.00')
        total_distance_payment = Decimal('0.00')

        for delivery in deliveries:
            payment = DeliveryPaymentService.calculate_payment(delivery)

            if payment:
                flat_rate = payment['flat_rate']
                distance_payment = payment['distance_payment']
                total_payment = payment['total']
            else:
                flat_rate = Decimal('0.00')
                distance_payment = Decimal('0.00')
                total_payment = Decimal('0.00')

            delivery_data.append({
                'id': delivery.id,
                'delivery_number': delivery.delivery_number,
                'order_number': delivery.order.order_number if delivery.order else None,
                'delivered_at': delivery.delivered_at.isoformat() if delivery.delivered_at else None,
                'address': delivery.address,
                'zone': delivery.zone.name if delivery.zone else None,
                'distance_km': str(delivery.delivered_distance_km) if delivery.delivered_distance_km else None,
                'flat_rate': str(flat_rate),
                'distance_payment': str(distance_payment),
                'total_payment': str(total_payment),
            })

            total_flat_rate += flat_rate
            total_distance_payment += distance_payment

        return JsonResponse({
            'contractor': {
                'id': contractor.id,
                'name': contractor.user.get_full_name() or contractor.user.username,
                'rfc': contractor.rfc,
                'curp': contractor.curp,
                'rate_per_delivery': str(contractor.rate_per_delivery) if contractor.rate_per_delivery else None,
                'rate_per_km': str(contractor.rate_per_km) if contractor.rate_per_km else None,
            },
            'deliveries': delivery_data,
            'totals': {
                'total_deliveries': len(delivery_data),
                'total_flat_rate': str(total_flat_rate),
                'total_distance_payment': str(total_distance_payment),
                'total_earnings': str(total_flat_rate + total_distance_payment),
            },
            'date_range': {
                'start_date': str(start_date),
                'end_date': str(end_date),
            }
        })

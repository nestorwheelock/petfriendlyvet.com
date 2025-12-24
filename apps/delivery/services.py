"""Services for the delivery app."""
import re
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.communications.models import MessageTemplate
from .models import Delivery, DeliveryDriver, DeliveryNotification, DeliveryZone


STATUS_TO_TEMPLATE = {
    'assigned': 'delivery_assigned',
    'picked_up': 'delivery_picked_up',
    'out_for_delivery': 'delivery_out_for_delivery',
    'arrived': 'delivery_arrived',
    'delivered': 'delivery_delivered',
    'failed': 'delivery_failed',
}


class DeliveryNotificationService:
    """Service for sending delivery notifications."""

    @classmethod
    def get_template_for_status(cls, status: str) -> Optional[MessageTemplate]:
        """Get the message template for a delivery status."""
        template_type = STATUS_TO_TEMPLATE.get(status)
        if not template_type:
            return None

        try:
            return MessageTemplate.objects.get(
                template_type=template_type,
                is_active=True
            )
        except MessageTemplate.DoesNotExist:
            return None

    @classmethod
    def render_message(
        cls,
        template_type: str,
        context: Dict[str, Any],
        language: str = 'es'
    ) -> str:
        """Render a message template with context variables."""
        try:
            template = MessageTemplate.objects.get(
                template_type=template_type,
                is_active=True
            )
        except MessageTemplate.DoesNotExist:
            return ''

        # Get the appropriate language body
        body = template.body_es if language == 'es' else template.body_en

        # Simple template variable replacement using {{variable}} syntax
        def replace_var(match):
            var_name = match.group(1)
            return str(context.get(var_name, ''))

        rendered = re.sub(r'\{\{(\w+)\}\}', replace_var, body)
        return rendered

    @classmethod
    def build_context(cls, delivery: Delivery) -> Dict[str, Any]:
        """Build context dictionary for template rendering."""
        context = {
            'delivery_number': delivery.delivery_number,
            'customer_name': delivery.order.user.get_full_name() or delivery.order.user.username,
            'address': delivery.address,
            'order_number': delivery.order.order_number,
        }

        # Add scheduled time info
        if delivery.scheduled_date:
            context['scheduled_date'] = delivery.scheduled_date.strftime('%d/%m/%Y')
        if delivery.scheduled_time_start and delivery.scheduled_time_end:
            context['scheduled_time'] = f"{delivery.scheduled_time_start.strftime('%H:%M')} - {delivery.scheduled_time_end.strftime('%H:%M')}"
            context['eta'] = context['scheduled_time']

        # Add driver info if assigned
        if delivery.driver:
            context['driver_name'] = delivery.driver.user.get_full_name() or delivery.driver.user.username
            if delivery.driver.phone:
                context['driver_phone'] = delivery.driver.phone

        # Add zone info
        if delivery.zone:
            context['zone_name'] = delivery.zone.name

        return context

    @classmethod
    def get_recipient_phone(cls, delivery: Delivery) -> Optional[str]:
        """Get the phone number to send notifications to."""
        # First try shipping_phone from order
        if hasattr(delivery.order, 'shipping_phone') and delivery.order.shipping_phone:
            return delivery.order.shipping_phone

        # Fall back to user's phone if available
        if hasattr(delivery.order.user, 'phone') and delivery.order.user.phone:
            return delivery.order.user.phone

        return None

    @classmethod
    def create_notification(
        cls,
        delivery: Delivery,
        notification_type: str,
        status: str
    ) -> Optional[DeliveryNotification]:
        """Create a notification record for a delivery status change."""
        template_type = STATUS_TO_TEMPLATE.get(status)
        if not template_type:
            return None

        recipient = cls.get_recipient_phone(delivery)
        if not recipient:
            return None

        context = cls.build_context(delivery)
        message = cls.render_message(template_type, context, language='es')

        if not message:
            return None

        notification = DeliveryNotification.objects.create(
            delivery=delivery,
            notification_type=notification_type,
            recipient=recipient,
            message=message,
            status='pending'
        )

        return notification

    @classmethod
    def send_status_notifications(
        cls,
        delivery: Delivery,
        new_status: str
    ) -> List[DeliveryNotification]:
        """Send all configured notifications for a status change."""
        notifications = []

        template = cls.get_template_for_status(new_status)
        if not template:
            return notifications

        # Get channels from template
        channels = template.channels or ['sms']

        for channel in channels:
            notification = cls.create_notification(
                delivery=delivery,
                notification_type=channel,
                status=new_status
            )
            if notification:
                notifications.append(notification)
                # In a real implementation, we would queue the actual send here
                # For now, mark as sent immediately
                notification.status = 'sent'
                notification.sent_at = timezone.now()
                notification.save()

        return notifications


class DeliveryAssignmentService:
    """Service for auto-assigning deliveries to drivers."""

    @classmethod
    def get_available_drivers_for_zone(cls, zone: DeliveryZone) -> List[DeliveryDriver]:
        """Get available drivers that cover a specific zone."""
        return list(DeliveryDriver.objects.filter(
            is_active=True,
            is_available=True,
            zones=zone
        ))

    @classmethod
    def get_driver_delivery_count_today(cls, driver: DeliveryDriver) -> int:
        """Get the number of deliveries assigned to a driver today."""
        today = date.today()
        return Delivery.objects.filter(
            driver=driver,
            scheduled_date=today,
            status__in=['assigned', 'picked_up', 'out_for_delivery', 'arrived', 'delivered']
        ).count()

    @classmethod
    def can_driver_accept_delivery(cls, driver: DeliveryDriver) -> bool:
        """Check if a driver can accept more deliveries today."""
        current_count = cls.get_driver_delivery_count_today(driver)
        return current_count < driver.max_deliveries_per_day

    @classmethod
    def get_best_driver_for_delivery(cls, delivery: Delivery) -> Optional[DeliveryDriver]:
        """Find the best available driver for a delivery."""
        if not delivery.zone:
            return None

        available_drivers = cls.get_available_drivers_for_zone(delivery.zone)

        # Filter drivers who can still accept deliveries
        eligible_drivers = [
            driver for driver in available_drivers
            if cls.can_driver_accept_delivery(driver)
        ]

        if not eligible_drivers:
            return None

        # Sort by current workload (least busy first) then by rating (highest first)
        drivers_with_count = []
        for driver in eligible_drivers:
            count = cls.get_driver_delivery_count_today(driver)
            drivers_with_count.append((driver, count))

        # Sort by count ascending, then by rating descending
        drivers_with_count.sort(key=lambda x: (x[1], -float(x[0].average_rating)))

        return drivers_with_count[0][0] if drivers_with_count else None

    @classmethod
    def auto_assign_pending(cls) -> List[Delivery]:
        """Auto-assign pending deliveries to available drivers."""
        today = date.today()
        assigned_deliveries = []

        # Get pending deliveries scheduled for today
        pending_deliveries = Delivery.objects.filter(
            status='pending',
            scheduled_date=today
        ).select_related('zone')

        for delivery in pending_deliveries:
            driver = cls.get_best_driver_for_delivery(delivery)
            if driver:
                delivery.driver = driver
                delivery.status = 'assigned'
                delivery.assigned_at = timezone.now()
                delivery.save()
                assigned_deliveries.append(delivery)

        return assigned_deliveries


class DeliveryPaymentService:
    """Service for calculating contractor delivery payments."""

    @classmethod
    def calculate_payment(cls, delivery: Delivery) -> Optional[Dict[str, Decimal]]:
        """Calculate payment for a single delivery.

        Returns dict with flat_rate, distance_payment, and total.
        Returns None if delivery has no driver.
        """
        if not delivery.driver:
            return None

        driver = delivery.driver

        # Employees don't get paid per delivery
        if driver.driver_type == 'employee':
            return {
                'flat_rate': Decimal('0.00'),
                'distance_payment': Decimal('0.00'),
                'total': Decimal('0.00'),
            }

        # Calculate flat rate
        flat_rate = driver.rate_per_delivery or Decimal('0.00')

        # Calculate distance payment
        distance_payment = Decimal('0.00')
        if driver.rate_per_km and delivery.delivered_distance_km:
            distance_payment = driver.rate_per_km * delivery.delivered_distance_km

        total = flat_rate + distance_payment

        return {
            'flat_rate': flat_rate,
            'distance_payment': distance_payment,
            'total': total,
        }

    @classmethod
    def calculate_driver_earnings(
        cls,
        driver: DeliveryDriver,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Calculate total earnings for a driver over a period.

        Returns dict with total_deliveries, total_earnings, breakdown.
        """
        # Get delivered deliveries in date range
        deliveries = Delivery.objects.filter(
            driver=driver,
            status='delivered',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        total_deliveries = deliveries.count()
        total_flat_rate = Decimal('0.00')
        total_distance_payment = Decimal('0.00')

        for delivery in deliveries:
            payment = cls.calculate_payment(delivery)
            if payment:
                total_flat_rate += payment['flat_rate']
                total_distance_payment += payment['distance_payment']

        total_earnings = total_flat_rate + total_distance_payment

        return {
            'total_deliveries': total_deliveries,
            'total_earnings': total_earnings,
            'total_flat_rate': total_flat_rate,
            'total_distance_payment': total_distance_payment,
        }

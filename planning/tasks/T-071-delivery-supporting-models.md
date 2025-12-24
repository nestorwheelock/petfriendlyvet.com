# T-071: Delivery Supporting Models

> **STOP! READ THIS FIRST:**
> Before writing ANY code, complete the [TDD STOP GATE](../TDD_STOP_GATE.md)
>
> You must output the confirmation block and write failing tests
> BEFORE any implementation code.

---

**Story**: S-027 - Delivery Module Core
**Priority**: High
**Status**: Pending
**Estimate**: 2 hours
**Dependencies**: T-070 (Delivery model)

---

## Objective

Create supporting models: DeliveryProof, DeliveryRating, and DeliveryNotification.

---

## Test Cases

```python
class DeliveryProofTests(TestCase):
    """Tests for DeliveryProof model."""

    def setUp(self):
        # Setup delivery...
        self.delivery = self._create_delivery()

    def test_create_photo_proof(self):
        """Can create photo proof of delivery."""
        proof = DeliveryProof.objects.create(
            delivery=self.delivery,
            proof_type='photo',
            recipient_name='Juan Garcia',
            latitude=Decimal('19.432608'),
            longitude=Decimal('-99.133209')
        )
        self.assertEqual(proof.proof_type, 'photo')
        self.assertEqual(proof.latitude, Decimal('19.432608'))

    def test_create_signature_proof(self):
        """Can create signature proof."""
        proof = DeliveryProof.objects.create(
            delivery=self.delivery,
            proof_type='signature',
            signature_data='data:image/png;base64,...',
            recipient_name='Maria Lopez'
        )
        self.assertEqual(proof.proof_type, 'signature')

    def test_proof_with_gps_coordinates(self):
        """Proof captures GPS from browser."""
        proof = DeliveryProof.objects.create(
            delivery=self.delivery,
            proof_type='photo',
            latitude=Decimal('19.432608'),
            longitude=Decimal('-99.133209'),
            gps_accuracy=Decimal('10.5')
        )
        self.assertIsNotNone(proof.latitude)
        self.assertIsNotNone(proof.longitude)


class DeliveryRatingTests(TestCase):
    """Tests for DeliveryRating model."""

    def setUp(self):
        self.delivery = self._create_delivery()

    def test_create_rating(self):
        """Can create delivery rating."""
        rating = DeliveryRating.objects.create(
            delivery=self.delivery,
            rating=5,
            feedback='Excellent service!'
        )
        self.assertEqual(rating.rating, 5)

    def test_rating_range_validation(self):
        """Rating must be 1-5."""
        with self.assertRaises(ValidationError):
            rating = DeliveryRating(delivery=self.delivery, rating=6)
            rating.full_clean()

    def test_one_rating_per_delivery(self):
        """Only one rating per delivery."""
        DeliveryRating.objects.create(delivery=self.delivery, rating=4)
        with self.assertRaises(IntegrityError):
            DeliveryRating.objects.create(delivery=self.delivery, rating=5)


class DeliveryNotificationTests(TestCase):
    """Tests for DeliveryNotification model."""

    def setUp(self):
        self.delivery = self._create_delivery()

    def test_create_notification(self):
        """Can create notification record."""
        notification = DeliveryNotification.objects.create(
            delivery=self.delivery,
            notification_type='status_update',
            channel='whatsapp',
            message='Your order is out for delivery'
        )
        self.assertEqual(notification.channel, 'whatsapp')
        self.assertIsNotNone(notification.sent_at)

    def test_notification_types(self):
        """Various notification types supported."""
        types = ['assigned', 'picked_up', 'out_for_delivery', 'arrived', 'delivered', 'failed']
        for ntype in types:
            DeliveryNotification.objects.create(
                delivery=self.delivery,
                notification_type=ntype,
                channel='sms'
            )
```

---

## Implementation

### Models

```python
PROOF_TYPES = [
    ('photo', 'Photo'),
    ('signature', 'Signature'),
    ('both', 'Photo and Signature'),
]

class DeliveryProof(models.Model):
    """Proof of delivery (photo, signature, GPS)."""

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='proofs'
    )
    proof_type = models.CharField(max_length=20, choices=PROOF_TYPES)

    # Photo proof
    image = models.ImageField(
        upload_to='delivery_proofs/%Y/%m/',
        null=True,
        blank=True
    )
    image_thumbnail = models.ImageField(
        upload_to='delivery_proofs/thumbs/%Y/%m/',
        null=True,
        blank=True
    )

    # Signature proof
    signature_data = models.TextField(
        blank=True,
        help_text="Base64 encoded signature image"
    )

    # Recipient info
    recipient_name = models.CharField(max_length=100, blank=True)

    # GPS from browser Geolocation API
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    gps_accuracy = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="GPS accuracy in meters"
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.delivery} - {self.get_proof_type_display()}"


class DeliveryRating(models.Model):
    """Customer rating of delivery experience."""

    delivery = models.OneToOneField(
        Delivery,
        on_delete=models.CASCADE,
        related_name='rating'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    feedback = models.TextField(blank=True)

    # What was rated
    driver_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    timeliness_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    package_condition_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.delivery} - {self.rating} stars"


NOTIFICATION_TYPES = [
    ('assigned', 'Driver Assigned'),
    ('picked_up', 'Order Picked Up'),
    ('out_for_delivery', 'Out for Delivery'),
    ('arrived', 'Driver Arrived'),
    ('delivered', 'Delivered'),
    ('failed', 'Delivery Failed'),
    ('rescheduled', 'Delivery Rescheduled'),
    ('eta_update', 'ETA Update'),
]

NOTIFICATION_CHANNELS = [
    ('sms', 'SMS'),
    ('whatsapp', 'WhatsApp'),
    ('email', 'Email'),
    ('push', 'Push Notification'),
]

class DeliveryNotification(models.Model):
    """Track sent notifications about delivery."""

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=20, choices=NOTIFICATION_CHANNELS)
    message = models.TextField(blank=True)

    # Status
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.delivery} - {self.get_notification_type_display()} ({self.channel})"
```

---

## Definition of Done

- [ ] DeliveryProof model with photo, signature, GPS
- [ ] DeliveryRating model with 1-5 rating, feedback
- [ ] DeliveryNotification model for tracking sent notifications
- [ ] Validators for rating range
- [ ] Unique constraint: one rating per delivery
- [ ] All tests pass (>95% coverage)
- [ ] Migrations created

"""Location models - Physical facilities/sites."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Location(models.Model):
    """Physical facility/site within the organization.

    Cross-cutting: EMR, appointments, inventory, HR all reference this.
    Single-tenant per deployment, multi-location within tenant.
    """

    # Organization reference (required, singleton in practice)
    organization = models.ForeignKey(
        'parties.Organization',
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name=_('organization'),
    )

    # Identity
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_('Display name, e.g., "Main Clinic", "North Branch"'),
    )
    code = models.CharField(
        _('code'),
        max_length=20,
        help_text=_('Stable identifier, e.g., "MAIN", "NORTH". Do not change after creation.'),
    )

    # Address (optional)
    address_line1 = models.CharField(_('address line 1'), max_length=255, blank=True)
    address_line2 = models.CharField(_('address line 2'), max_length=255, blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state/province'), max_length=100, blank=True)
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    country = models.CharField(_('country'), max_length=100, default='Mexico')

    # Operations
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        default='America/Cancun',
        help_text=_('IANA timezone, e.g., "America/Cancun", "America/Mexico_City"'),
    )
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)

    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        db_index=True,
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'code'],
                name='uniq_location_code_per_org',
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def full_address(self):
        """Returns formatted full address."""
        parts = []
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)
        if self.city or self.state or self.postal_code:
            city_line = f'{self.city}, {self.state} {self.postal_code}'.strip(' ,')
            parts.append(city_line)
        if self.country:
            parts.append(self.country)
        return '\n'.join(parts) if parts else ''


class ExamRoom(models.Model):
    """Exam rooms belonging to a location.

    Policy: Rooms are SOFT-DEACTIVATED (is_active=False), never deleted.
    This preserves historical encounter references.
    """

    location = models.ForeignKey(
        'Location',
        on_delete=models.CASCADE,
        related_name='exam_rooms',
        verbose_name=_('location'),
    )
    name = models.CharField(
        _('name'),
        max_length=30,
        help_text=_('Room identifier, e.g., "Room 1", "Exam A", "Surgery"'),
    )

    ROOM_TYPES = [
        ('exam', _('Exam Room')),
        ('surgery', _('Surgery')),
        ('imaging', _('Imaging')),
        ('treatment', _('Treatment')),
        ('isolation', _('Isolation')),
    ]
    room_type = models.CharField(
        _('room type'),
        max_length=20,
        choices=ROOM_TYPES,
        default='exam',
    )

    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Set to False to retire a room without deleting'),
    )
    display_order = models.PositiveIntegerField(
        _('display order'),
        default=0,
        help_text=_('Order in room selection lists (lower first)'),
    )

    class Meta:
        verbose_name = _('exam room')
        verbose_name_plural = _('exam rooms')
        ordering = ['display_order', 'name']
        unique_together = [['location', 'name']]
        indexes = [
            models.Index(fields=['location', 'is_active', 'display_order']),
        ]

    def __str__(self):
        return self.name

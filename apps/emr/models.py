"""EMR models - Canonical clinical models per SYSTEM_CHARTER.md.

Key Design Principles:
1. Encounter is the aggregate root - all clinical activity links to Encounter
2. Medical records are append-only with soft corrections (never delete)
3. Every EMR record is scoped by parties.Organization (multi-tenant)
4. Uses explicit FKs per PARTIES.md pattern (NOT GenericForeignKey)
5. RBAC enforced via @require_permission('emr', action)
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


# =============================================================================
# Encounter - The Aggregate Root
# =============================================================================

class Encounter(models.Model):
    """Central EMR anchor - every clinical activity hangs off this.

    Per SYSTEM_CHARTER.md: "Encounter (Consultation) is the aggregate root."

    Pipeline states track patient flow through the clinic.
    Walk-ins have no appointment link.
    """

    # Location where encounter takes place (required)
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='encounters',
        verbose_name=_('location'),
        help_text=_('Facility/site where this encounter occurs'),
    )
    # Organization derived via self.location.organization (not stored)

    # Link to scheduling (optional - walk-ins have no appointment)
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encounter',
        verbose_name=_('appointment'),
    )

    # Link to patient (via PatientRecord, not Pet directly)
    patient = models.ForeignKey(
        'practice.PatientRecord',
        on_delete=models.CASCADE,
        related_name='encounters',
        verbose_name=_('patient'),
    )

    # Pipeline states for workflow tracking
    PIPELINE_STATES = [
        ('scheduled', _('Scheduled')),
        ('checked_in', _('Checked In')),
        ('roomed', _('Roomed')),
        ('in_exam', _('In Exam')),
        ('pending_orders', _('Pending Orders')),
        ('awaiting_results', _('Awaiting Results')),
        ('treatment', _('Treatment')),
        ('checkout', _('Checkout')),
        ('completed', _('Completed')),
        ('no_show', _('No Show')),
        ('cancelled', _('Cancelled')),
    ]
    pipeline_state = models.CharField(
        _('pipeline state'),
        max_length=20,
        choices=PIPELINE_STATES,
        default='scheduled',
        db_index=True,
    )

    # State transition timestamps
    scheduled_at = models.DateTimeField(_('scheduled at'), null=True, blank=True)
    checked_in_at = models.DateTimeField(_('checked in at'), null=True, blank=True)
    roomed_at = models.DateTimeField(_('roomed at'), null=True, blank=True)
    exam_started_at = models.DateTimeField(_('exam started at'), null=True, blank=True)
    exam_ended_at = models.DateTimeField(_('exam ended at'), null=True, blank=True)
    discharged_at = models.DateTimeField(_('discharged at'), null=True, blank=True)

    # Staff assignment
    assigned_vet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encounters_as_vet',
        verbose_name=_('assigned veterinarian'),
    )
    assigned_tech = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encounters_as_tech',
        verbose_name=_('assigned technician'),
    )
    room = models.CharField(
        _('room'),
        max_length=50,
        blank=True,
        help_text=_('LEGACY: Use exam_room FK instead'),
    )
    exam_room = models.ForeignKey(
        'locations.ExamRoom',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='encounters',
        verbose_name=_('exam room'),
        help_text=_('Assigned exam room from location'),
    )

    # Encounter classification
    ENCOUNTER_TYPES = [
        ('routine', _('Routine/Wellness')),
        ('urgent', _('Urgent Care')),
        ('emergency', _('Emergency')),
        ('follow_up', _('Follow-up')),
        ('telehealth', _('Telehealth')),
        ('surgery', _('Surgery')),
        ('dental', _('Dental')),
        ('grooming', _('Grooming')),
        ('boarding', _('Boarding')),
        ('other', _('Other')),
    ]
    encounter_type = models.CharField(
        _('encounter type'),
        max_length=20,
        choices=ENCOUNTER_TYPES,
        default='routine',
    )
    chief_complaint = models.TextField(
        _('chief complaint'),
        blank=True,
        help_text=_('Primary reason for visit'),
    )

    # Billing link (populated at checkout)
    invoice = models.ForeignKey(
        'billing.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encounters',
        verbose_name=_('invoice'),
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encounters_created',
        verbose_name=_('created by'),
    )

    class Meta:
        verbose_name = _('encounter')
        verbose_name_plural = _('encounters')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['location', '-created_at']),
            models.Index(fields=['location', 'pipeline_state']),
            models.Index(fields=['patient', '-created_at']),
        ]

    def __str__(self):
        return f"Encounter #{self.pk} - {self.patient} ({self.get_pipeline_state_display()})"

    @property
    def organization(self):
        """Derive organization from location."""
        if self.location_id is None:
            return None
        return self.location.organization

    @property
    def is_active(self):
        """Returns True if encounter is in an active (not terminal) state."""
        return self.pipeline_state not in ('completed', 'no_show', 'cancelled')


# =============================================================================
# PatientProblem - Cross-Encounter Continuity
# =============================================================================

class PatientProblem(models.Model):
    """Active problems/diagnoses that persist across encounters.

    Patient-level (not encounter-level or location-scoped).
    Used for allergies, chronic conditions, behavioral alerts.

    Invariant: if is_alert=True, alert_text is required.
    Enforced in forms/admin; use service functions for programmatic writes.
    """

    # Patient this problem belongs to (patient-level, not location-scoped)
    patient = models.ForeignKey(
        'practice.PatientRecord',
        on_delete=models.CASCADE,
        related_name='problems',
        verbose_name=_('patient'),
    )

    # TODO: Future - track where problem was recorded
    # recorded_at_location = models.ForeignKey(
    #     'locations.Location', null=True, blank=True, on_delete=models.SET_NULL
    # )

    # Problem classification (use is_alert flag for alerts, not problem_type)
    PROBLEM_TYPES = [
        ('diagnosis', _('Diagnosis')),
        ('allergy', _('Allergy')),
        ('chronic', _('Chronic Condition')),
        ('behavioral', _('Behavioral')),
        ('other', _('Other')),
    ]
    problem_type = models.CharField(
        _('problem type'),
        max_length=20,
        choices=PROBLEM_TYPES,
        default='diagnosis',
    )

    SEVERITY_LEVELS = [
        ('low', _('Low')),
        ('moderate', _('Moderate')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]
    severity = models.CharField(
        _('severity'),
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='moderate',
    )

    # Problem details
    name = models.CharField(
        _('name'),
        max_length=200,
        help_text=_('e.g., "Diabetes Mellitus Type II", "Penicillin Allergy"'),
    )
    description = models.TextField(
        _('description'),
        blank=True,
    )

    # Lifecycle
    onset_date = models.DateField(
        _('onset date'),
        null=True,
        blank=True,
        help_text=_('When the problem was first identified'),
    )
    resolved_date = models.DateField(
        _('resolved date'),
        null=True,
        blank=True,
        help_text=_('When the problem was resolved (if applicable)'),
    )

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('controlled', _('Controlled')),
        ('resolved', _('Resolved')),
        ('inactive', _('Inactive')),
    ]
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )

    # Alert display (for header banners in UI)
    is_alert = models.BooleanField(
        _('show as alert'),
        default=False,
        help_text=_('Display prominently in patient header'),
    )
    alert_text = models.CharField(
        _('alert text'),
        max_length=100,
        blank=True,
        help_text=_('Short text for alert banner, e.g., "ALLERGIC TO PENICILLIN"'),
    )

    ALERT_SEVERITY = [
        ('info', _('Info')),
        ('warning', _('Warning')),
        ('danger', _('Danger')),
    ]
    alert_severity = models.CharField(
        _('alert severity'),
        max_length=10,
        choices=ALERT_SEVERITY,
        default='warning',
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='problems_created',
        verbose_name=_('created by'),
    )

    class Meta:
        verbose_name = _('patient problem')
        verbose_name_plural = _('patient problems')
        ordering = ['-is_alert', '-severity', 'name']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['is_alert']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def clean(self):
        """Validate invariants.

        Enforced in forms/admin; use service functions for programmatic writes.
        """
        from django.core.exceptions import ValidationError
        if self.is_alert and not self.alert_text:
            raise ValidationError({
                'alert_text': _('Alert text is required when "show as alert" is enabled.')
            })


# =============================================================================
# ClinicalEvent - Append-Only Timeline
# =============================================================================

class ClinicalEvent(models.Model):
    """Immutable event log for timeline views.

    Key principle: APPEND-ONLY. Never delete or update content.
    Use 'entered_in_error' for corrections via mark_as_error() method.

    Per SYSTEM_CHARTER.md: "Medical records are append-only with soft corrections."
    Per PARTIES.md: Uses explicit nullable FKs, NOT GenericForeignKey.

    Scoping: patient required; encounter optional; location optional; org derived.

    IMPORTANT: Append-only enforced at application layer via save() override.
    QuerySet.update() and raw SQL bypass this - use service functions only.
    Admin edit permissions should be restricted to error correction fields.
    """

    # Patient context (required)
    patient = models.ForeignKey(
        'practice.PatientRecord',
        on_delete=models.CASCADE,
        related_name='clinical_events',
        verbose_name=_('patient'),
    )

    # Encounter context (optional - null for patient-level events)
    encounter = models.ForeignKey(
        'Encounter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinical_events',
        verbose_name=_('encounter'),
        help_text=_('Encounter this event occurred during (if any)'),
    )

    # Location provenance (optional - where was this recorded)
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinical_events',
        verbose_name=_('location'),
        help_text=_('Where this event was recorded (auto-set from encounter if present)'),
    )
    # Organization derived via self.organization property (not stored)

    # Event classification
    EVENT_TYPES = [
        ('encounter_created', _('Encounter Created')),
        ('state_change', _('Pipeline State Change')),
        ('problem_added', _('Problem Added')),
        ('problem_resolved', _('Problem Resolved')),
        ('note', _('Clinical Note')),
        # Future phases will add: vital, soap, lab_order, lab_result, etc.
    ]
    event_type = models.CharField(
        _('event type'),
        max_length=30,
        choices=EVENT_TYPES,
        db_index=True,
    )
    event_subtype = models.CharField(
        _('event subtype'),
        max_length=50,
        blank=True,
        help_text=_('Additional classification (e.g., state transition name)'),
    )

    # Timestamps
    occurred_at = models.DateTimeField(
        _('occurred at'),
        help_text=_('When the clinical event occurred'),
        db_index=True,
    )
    recorded_at = models.DateTimeField(
        _('recorded at'),
        auto_now_add=True,
        help_text=_('When the event was recorded in system'),
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='clinical_events_recorded',
        verbose_name=_('recorded by'),
    )

    # EXPLICIT FKs to related records (nullable, per PARTIES.md pattern)
    # Only ONE of these should be set per event (based on event_type)
    patient_problem = models.ForeignKey(
        'PatientProblem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinical_events',
        verbose_name=_('patient problem'),
    )
    # Future phases will add: vital_signs, soap_note, lab_order, lab_result, etc.

    # Denormalized summary for fast timeline display
    summary = models.CharField(
        _('summary'),
        max_length=500,
        help_text=_('Human-readable summary for timeline display'),
    )
    is_significant = models.BooleanField(
        _('significant'),
        default=False,
        help_text=_('Mark as significant for filtering important events'),
    )

    # Soft correction (NEVER delete medical records - append only)
    is_entered_in_error = models.BooleanField(
        _('entered in error'),
        default=False,
        help_text=_('Mark as entered in error (original stays, this flags it)'),
    )
    error_corrected_at = models.DateTimeField(
        _('error corrected at'),
        null=True,
        blank=True,
    )
    error_corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emr_corrections',
        verbose_name=_('error corrected by'),
    )
    error_correction_reason = models.TextField(
        _('correction reason'),
        blank=True,
        help_text=_('Reason for marking as entered in error'),
    )
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supersedes',
        verbose_name=_('superseded by'),
        help_text=_('Link to corrected version of this event'),
    )

    class Meta:
        verbose_name = _('clinical event')
        verbose_name_plural = _('clinical events')
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['patient', '-occurred_at']),
            models.Index(fields=['encounter', '-occurred_at']),
            models.Index(fields=['location', '-occurred_at']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.summary[:50]}"

    @property
    def organization(self):
        """Derive organization from encounter or location."""
        if self.encounter_id:
            return self.encounter.organization
        if self.location_id:
            return self.location.organization
        return None

    # =========================================================================
    # APPEND-ONLY ENFORCEMENT
    # =========================================================================

    # Fields that CAN be updated (error correction only)
    _MUTABLE_FIELDS = frozenset([
        'is_entered_in_error',
        'error_corrected_at',
        'error_corrected_by',
        'error_correction_reason',
        'superseded_by',
    ])

    def save(self, *args, **kwargs):
        """Enforce append-only: new records allowed, updates restricted.

        Only error correction fields can be updated after creation.
        Use mark_as_error() for corrections, not direct save().
        """
        if self.pk:
            # Existing record - only allow error correction field updates
            update_fields = kwargs.get('update_fields')
            if update_fields:
                # Check that only mutable fields are being updated
                updating = set(update_fields)
                forbidden = updating - self._MUTABLE_FIELDS
                if forbidden:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(
                        f"ClinicalEvent is append-only. Cannot update: {forbidden}"
                    )
            else:
                # Full save on existing record - not allowed
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    "ClinicalEvent is append-only. Use mark_as_error() for corrections."
                )
        else:
            # New record - auto-set location from encounter if not provided
            if self.encounter_id and not self.location_id:
                self.location = self.encounter.location
        super().save(*args, **kwargs)

    def mark_as_error(self, user, reason):
        """Mark this event as entered in error.

        Per SYSTEM_CHARTER: Never delete, use soft correction.
        """
        from django.utils import timezone
        self.is_entered_in_error = True
        self.error_corrected_at = timezone.now()
        self.error_corrected_by = user
        self.error_correction_reason = reason
        self.save(update_fields=[
            'is_entered_in_error',
            'error_corrected_at',
            'error_corrected_by',
            'error_correction_reason',
        ])

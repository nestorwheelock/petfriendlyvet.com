# T-018: Migration Models & Tracking

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement migration tracking models and utilities
**Related Story**: S-023
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/migration/, apps/core/
**Forbidden Paths**: None

### Deliverables
- [ ] Migration batch model
- [ ] Migration record model
- [ ] Error logging model
- [ ] Progress tracking
- [ ] Rollback support
- [ ] Validation utilities

### Implementation Details

#### Models
```python
class MigrationBatch(models.Model):
    """Track a migration import batch."""

    SOURCES = [
        ('okvet', 'OkVet.co'),
        ('csv', 'CSV Import'),
        ('manual', 'Manual Entry'),
    ]

    STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ]

    source = models.CharField(max_length=50, choices=SOURCES)
    source_file = models.FileField(upload_to='migrations/', null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')

    # Stats
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    skip_count = models.IntegerField(default=0)

    # Metadata
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # Options
    dry_run = models.BooleanField(default=True)
    stop_on_error = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Migration Batches"


class MigrationRecord(models.Model):
    """Track individual record migration."""

    RECORD_TYPES = [
        ('client', 'Client'),
        ('pet', 'Pet'),
        ('medical_record', 'Medical Record'),
        ('vaccination', 'Vaccination'),
        ('appointment', 'Appointment'),
        ('invoice', 'Invoice'),
    ]

    STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('skipped', 'Skipped'),
        ('rolled_back', 'Rolled Back'),
    ]

    batch = models.ForeignKey(
        MigrationBatch,
        on_delete=models.CASCADE,
        related_name='records'
    )
    record_type = models.CharField(max_length=50, choices=RECORD_TYPES)
    source_id = models.CharField(max_length=255)  # ID in source system
    status = models.CharField(max_length=20, choices=STATUS, default='pending')

    # Result tracking
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.IntegerField(null=True)  # ID in our system

    # Data storage
    source_data = models.JSONField(default=dict)
    transformed_data = models.JSONField(default=dict)

    # Error tracking
    error_message = models.TextField(blank=True)
    error_field = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class MigrationFieldMapping(models.Model):
    """Store field mappings for migration."""

    source_system = models.CharField(max_length=50)
    record_type = models.CharField(max_length=50)
    source_field = models.CharField(max_length=100)
    target_field = models.CharField(max_length=100)
    transform = models.CharField(max_length=255, blank=True)  # e.g., 'date_parse', 'phone_format'
    is_required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ['source_system', 'record_type', 'source_field']
```

#### Transform Utilities
```python
class FieldTransformer:
    """Transform field values during migration."""

    @staticmethod
    def date_parse(value: str) -> date:
        """Parse various date formats."""
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%m/%d/%Y',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: {value}")

    @staticmethod
    def phone_format(value: str) -> str:
        """Format phone number to +52 format."""
        digits = re.sub(r'\D', '', value)
        if len(digits) == 10:
            return f"+52{digits}"
        elif len(digits) == 12 and digits.startswith('52'):
            return f"+{digits}"
        return value

    @staticmethod
    def species_map(value: str) -> str:
        """Map species names to standard values."""
        mapping = {
            'perro': 'dog',
            'gato': 'cat',
            'ave': 'bird',
            'conejo': 'rabbit',
            'hamster': 'hamster',
        }
        return mapping.get(value.lower(), 'other')
```

#### Validation Utilities
```python
class MigrationValidator:
    """Validate records before migration."""

    def validate_client(self, data: dict) -> list[str]:
        """Validate client data."""
        errors = []
        if not data.get('name') and not data.get('first_name'):
            errors.append("Name is required")
        if data.get('email') and not self._valid_email(data['email']):
            errors.append("Invalid email format")
        if data.get('phone') and not self._valid_phone(data['phone']):
            errors.append("Invalid phone format")
        return errors

    def validate_pet(self, data: dict) -> list[str]:
        """Validate pet data."""
        errors = []
        if not data.get('name'):
            errors.append("Pet name is required")
        if not data.get('species'):
            errors.append("Species is required")
        return errors
```

### Test Cases
- [ ] Batch creation and tracking
- [ ] Record migration with success
- [ ] Record migration with error
- [ ] Field transformations work
- [ ] Validation catches errors
- [ ] Progress updates correctly
- [ ] Rollback restores state

### Definition of Done
- [ ] All models migrated
- [ ] Transformers tested
- [ ] Validators complete
- [ ] Progress tracking works
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-001: Django Project Setup
- T-017: OkVet Export Research

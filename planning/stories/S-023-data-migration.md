# S-023: Data Migration (OkVet.co Import)

**Story Type:** User Story
**Priority:** CRITICAL
**Epoch:** 1 (Foundation)
**Status:** PENDING
**Module:** Management commands + one-time scripts

## User Story

**As a** clinic owner
**I want to** migrate all existing data from OkVet.co
**So that** I don't lose years of client and patient records

**As a** pet owner
**I want to** see my pet's complete history in the new system
**So that** I have continuity of care records

**As a** veterinarian
**I want to** access historical medical records
**So that** I can provide informed care based on pet history

## Critical Importance

**This is the MOST CRITICAL story for launch readiness.**

Dr. Pablo has years of data in OkVet.co:
- Client/owner records
- Pet profiles and medical histories
- Vaccination records
- Appointment history
- Invoice/billing history

**Without successful migration, the new system cannot launch.**

## Acceptance Criteria

### Data Export from OkVet.co
- [ ] Research OkVet.co export options (CSV, API, manual)
- [ ] Document OkVet.co data structure
- [ ] Obtain sample export files from Dr. Pablo
- [ ] Identify all exportable data types
- [ ] Document any data that cannot be exported

### Data Mapping
- [ ] Map OkVet.co fields to our models
- [ ] Identify required transformations
- [ ] Document data type conversions
- [ ] Plan for missing/optional fields
- [ ] Handle date/time format differences

### Data to Migrate

| Data Type | Priority | Source | Destination |
|-----------|----------|--------|-------------|
| Clients/Owners | Critical | OkVet clients | User + OwnerProfile |
| Pets | Critical | OkVet patients | Pet model |
| Medical History | Critical | OkVet records | MedicalRecord |
| Vaccinations | Critical | OkVet vaccines | VaccinationRecord |
| Appointments | High | OkVet schedule | Appointment (historical) |
| Invoices | High | OkVet billing | Invoice (historical) |
| Products | Medium | OkVet inventory | Product |
| Documents/Photos | Medium | OkVet attachments | Document/Media |

### Migration Process
- [ ] Validation and data cleaning scripts
- [ ] Duplicate detection and handling
- [ ] Data transformation scripts
- [ ] Import scripts with rollback capability
- [ ] Progress reporting during import
- [ ] Error logging and reporting
- [ ] Dry-run mode for testing

### Data Integrity
- [ ] Maintain referential integrity (owner → pet → records)
- [ ] Preserve original IDs as external_id for reference
- [ ] Handle orphaned records gracefully
- [ ] Validate required fields
- [ ] Log all data quality issues

### Post-Migration Verification
- [ ] Record count verification (source vs destination)
- [ ] Spot-check random records
- [ ] Verify relationships maintained
- [ ] Side-by-side comparison reports
- [ ] Missing data identification
- [ ] Manual correction tools

## Technical Requirements

### Models (Migration Support)

```python
class MigrationBatch(models.Model):
    """Track migration batch runs"""
    BATCH_TYPES = [
        ('clients', 'Clients/Owners'),
        ('pets', 'Pets'),
        ('medical', 'Medical Records'),
        ('vaccines', 'Vaccinations'),
        ('appointments', 'Appointments'),
        ('invoices', 'Invoices'),
        ('products', 'Products'),
        ('documents', 'Documents'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ]

    batch_type = models.CharField(max_length=20, choices=BATCH_TYPES)
    source_file = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Counts
    total_records = models.IntegerField(default=0)
    imported_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    duplicate_count = models.IntegerField(default=0)

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Dry run
    is_dry_run = models.BooleanField(default=False)

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']


class MigrationRecord(models.Model):
    """Individual record migration tracking"""
    batch = models.ForeignKey(MigrationBatch, on_delete=models.CASCADE, related_name='records')

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('imported', 'Imported'),
        ('skipped', 'Skipped'),
        ('error', 'Error'),
        ('duplicate', 'Duplicate'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Source data
    source_id = models.CharField(max_length=100)  # OkVet ID
    source_data = models.JSONField(default=dict)  # Original row

    # Destination
    target_model = models.CharField(max_length=100)
    target_id = models.IntegerField(null=True, blank=True)  # Our ID

    # Errors
    error_message = models.TextField(blank=True)
    validation_errors = models.JSONField(default=list)

    # Duplicate info
    duplicate_of = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class ExternalIdMapping(models.Model):
    """Map external IDs to internal IDs for reference"""
    source_system = models.CharField(max_length=50, default='okvet')
    source_type = models.CharField(max_length=50)  # client, pet, record, etc.
    source_id = models.CharField(max_length=100)

    target_model = models.CharField(max_length=100)
    target_id = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['source_system', 'source_type', 'source_id']
        indexes = [
            models.Index(fields=['source_system', 'source_type', 'source_id']),
            models.Index(fields=['target_model', 'target_id']),
        ]


class DataQualityIssue(models.Model):
    """Track data quality issues found during migration"""
    SEVERITY_CHOICES = [
        ('critical', 'Critical - Must Fix'),
        ('warning', 'Warning - Should Review'),
        ('info', 'Info - For Reference'),
    ]

    batch = models.ForeignKey(MigrationBatch, on_delete=models.CASCADE, related_name='issues')
    record = models.ForeignKey(MigrationRecord, on_delete=models.CASCADE, null=True, blank=True)

    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    issue_type = models.CharField(max_length=100)
    # missing_required, invalid_format, orphaned_record, duplicate, etc.

    field_name = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    source_value = models.TextField(blank=True)

    # Resolution
    resolved = models.BooleanField(default=False)
    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

### Management Commands

```python
# Usage examples:

# 1. Validate source data (dry run)
python manage.py import_okvet_clients --file=clients.csv --dry-run

# 2. Import with rollback capability
python manage.py import_okvet_clients --file=clients.csv

# 3. Import pets (requires clients first)
python manage.py import_okvet_pets --file=pets.csv

# 4. Import medical records (requires pets)
python manage.py import_okvet_records --file=medical_history.csv

# 5. Import vaccinations
python manage.py import_okvet_vaccines --file=vaccines.csv

# 6. Verify migration
python manage.py verify_migration --report=migration_report.html

# 7. Rollback if needed
python manage.py rollback_migration --batch-id=123

# 8. Generate comparison report
python manage.py compare_migration --output=comparison.html
```

### Command Implementation Pattern

```python
# core/management/commands/import_okvet_clients.py

from django.core.management.base import BaseCommand
import csv
from migration.models import MigrationBatch, MigrationRecord, ExternalIdMapping
from accounts.models import User
from vet_clinic.models import OwnerProfile

class Command(BaseCommand):
    help = 'Import clients from OkVet.co export'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='CSV file path')
        parser.add_argument('--dry-run', action='store_true', help='Validate only')
        parser.add_argument('--skip-duplicates', action='store_true')
        parser.add_argument('--batch-size', type=int, default=100)

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        # Create batch record
        batch = MigrationBatch.objects.create(
            batch_type='clients',
            source_file=file_path,
            is_dry_run=dry_run,
            status='running'
        )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    batch.total_records += 1
                    self.process_row(row, batch, dry_run)

            batch.status = 'completed'

        except Exception as e:
            batch.status = 'failed'
            batch.notes = str(e)
            raise

        finally:
            batch.completed_at = timezone.now()
            batch.save()

        self.report_results(batch)

    def process_row(self, row, batch, dry_run):
        """Process a single client row"""
        record = MigrationRecord.objects.create(
            batch=batch,
            source_id=row.get('id', ''),
            source_data=row
        )

        try:
            # Validate
            errors = self.validate_row(row)
            if errors:
                record.validation_errors = errors
                record.status = 'error'
                record.error_message = '; '.join(errors)
                batch.error_count += 1
                return

            # Check for duplicates
            if self.is_duplicate(row):
                record.status = 'duplicate'
                batch.duplicate_count += 1
                return

            if dry_run:
                record.status = 'pending'
                return

            # Create user and owner profile
            user, owner = self.create_owner(row)

            # Store mapping
            ExternalIdMapping.objects.create(
                source_system='okvet',
                source_type='client',
                source_id=row['id'],
                target_model='User',
                target_id=user.id
            )

            record.target_model = 'User'
            record.target_id = user.id
            record.status = 'imported'
            batch.imported_count += 1

        except Exception as e:
            record.status = 'error'
            record.error_message = str(e)
            batch.error_count += 1

        finally:
            record.save()

    def validate_row(self, row):
        """Validate required fields and formats"""
        errors = []

        if not row.get('nombre'):
            errors.append('Missing required field: nombre')

        if not row.get('telefono') and not row.get('email'):
            errors.append('Must have phone or email')

        # Validate email format
        email = row.get('email', '')
        if email and not self.is_valid_email(email):
            errors.append(f'Invalid email format: {email}')

        return errors

    def is_duplicate(self, row):
        """Check if this client already exists"""
        email = row.get('email')
        phone = row.get('telefono')

        if email and User.objects.filter(email=email).exists():
            return True

        if phone and OwnerProfile.objects.filter(phone=phone).exists():
            return True

        return False

    def create_owner(self, row):
        """Create User and OwnerProfile from row data"""
        # Transform data
        email = row.get('email') or f"imported_{row['id']}@placeholder.local"

        user = User.objects.create(
            email=email,
            first_name=row.get('nombre', '').split()[0],
            last_name=' '.join(row.get('nombre', '').split()[1:]),
            is_active=True,
        )

        owner = OwnerProfile.objects.create(
            user=user,
            phone=row.get('telefono', ''),
            address=row.get('direccion', ''),
            notes=f"Imported from OkVet.co. Original ID: {row['id']}",
        )

        return user, owner
```

### Field Mapping Reference

```python
# Expected OkVet.co field mappings (to be confirmed with actual export)

OKVET_CLIENT_MAPPING = {
    'id': 'external_id',
    'nombre': 'full_name',  # Split into first/last
    'telefono': 'phone',
    'celular': 'mobile',
    'email': 'email',
    'direccion': 'address',
    'ciudad': 'city',
    'notas': 'notes',
    'fecha_registro': 'created_at',
}

OKVET_PET_MAPPING = {
    'id': 'external_id',
    'id_cliente': 'owner_external_id',  # Link to owner
    'nombre': 'name',
    'especie': 'species',
    'raza': 'breed',
    'sexo': 'sex',
    'fecha_nacimiento': 'birth_date',
    'peso': 'weight',
    'color': 'color',
    'microchip': 'microchip_number',
    'esterilizado': 'is_sterilized',
    'fallecido': 'is_deceased',
    'notas': 'notes',
}

OKVET_RECORD_MAPPING = {
    'id': 'external_id',
    'id_paciente': 'pet_external_id',
    'fecha': 'date',
    'tipo': 'record_type',
    'descripcion': 'description',
    'diagnostico': 'diagnosis',
    'tratamiento': 'treatment',
    'notas': 'notes',
    'id_veterinario': 'vet_external_id',
}

OKVET_VACCINE_MAPPING = {
    'id': 'external_id',
    'id_paciente': 'pet_external_id',
    'vacuna': 'vaccine_name',
    'fecha_aplicacion': 'date_given',
    'fecha_proxima': 'next_due_date',
    'lote': 'lot_number',
    'laboratorio': 'manufacturer',
    'id_veterinario': 'administered_by',
}
```

## Migration Phases

### Phase 1: Research & Preparation
1. Contact OkVet.co support about export options
2. Obtain sample exports from Dr. Pablo
3. Document actual data structure
4. Identify data volume (record counts)
5. Plan migration timeline

### Phase 2: Development
1. Build import commands
2. Build validation rules
3. Build duplicate detection
4. Build rollback mechanism
5. Create dry-run mode

### Phase 3: Testing
1. Import into development environment
2. Run full validation
3. Fix data quality issues
4. Verify record counts
5. Test all record types

### Phase 4: Production Migration
1. Schedule downtime window
2. Final OkVet.co export
3. Run production import
4. Verify completeness
5. Enable new system

### Phase 5: Verification
1. Side-by-side comparison
2. Random spot checks
3. User acceptance testing
4. Fix any issues found
5. Sign-off from Dr. Pablo

## Verification Reports

### Record Count Report
```
═══════════════════════════════════════
MIGRATION VERIFICATION REPORT
═══════════════════════════════════════
Date: [Date]
Source: OkVet.co
Destination: Pet-Friendly v1.0

RECORD COUNTS:
                    Source    Imported    Diff
Clients/Owners:     1,234     1,230       -4*
Pets:               2,456     2,450       -6*
Medical Records:   12,345    12,340       -5*
Vaccinations:       5,678     5,678        0
Appointments:       8,901     8,901        0
Invoices:           6,789     6,785       -4*

* See data quality issues for details

DATA QUALITY ISSUES:
- 4 clients without valid contact info (skipped)
- 6 pets with orphaned owner references (flagged)
- 5 medical records with date format errors (corrected)

VERIFICATION CHECKLIST:
✅ All clients with valid data imported
✅ All pets linked to correct owners
✅ Medical history complete for all pets
✅ Vaccination records current
✅ Invoice history preserved

SIGN-OFF:
□ Data verified by: ________________
□ Date: ________________
═══════════════════════════════════════
```

## Definition of Done

- [ ] OkVet.co export format documented
- [ ] All import management commands created
- [ ] Dry-run validation mode working
- [ ] Rollback capability implemented
- [ ] Duplicate detection working
- [ ] External ID mapping preserved
- [ ] All data types successfully imported
- [ ] Verification reports generated
- [ ] Data quality issues logged and resolved
- [ ] Dr. Pablo sign-off on migrated data
- [ ] Tests written and passing (>95% coverage)

## Dependencies

- S-001: Foundation (models must exist)
- S-003: Pet Profiles (Pet model)
- S-007: CRM (OwnerProfile)

## Research Needed

1. **OkVet.co Export Options**
   - Does OkVet.co provide CSV/Excel export?
   - Is there an API for data extraction?
   - What are the export limitations?
   - Contact: support@okvet.co

2. **Data Volume**
   - How many clients in OkVet.co?
   - How many pets?
   - How many medical records?
   - How many years of history?

3. **Data Quality**
   - Sample data inspection
   - Common data quality issues
   - Missing required fields

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| OkVet.co doesn't support export | High | Manual entry, screen scraping |
| Data format unexpected | Medium | Flexible parsers, manual mapping |
| Duplicate/inconsistent data | Medium | Deduplication rules, manual review |
| Missing historical data | High | Phased approach, partial migration |
| Migration window too small | Medium | Off-hours migration, incremental sync |

## Notes

- **THIS MUST BE COMPLETED BEFORE LAUNCH**
- Start research immediately after project approval
- Get sample exports from Dr. Pablo ASAP
- Plan for at least 2 full test migrations before production
- Consider parallel run period (both systems active)
- Keep OkVet.co accessible for reference during transition

## Development Process

**Before implementing this story**, review and follow the **23-Step TDD Cycle** in:
- `CLAUDE.md` - Global development workflow
- `planning/TASK_BREAKDOWN.md` - Specific tasks for this story

Tests must be written before implementation. >95% coverage required.

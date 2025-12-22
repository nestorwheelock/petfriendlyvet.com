# T-019: Client Import Command

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement management command to import clients from OkVet.co
**Related Story**: S-023
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/migration/, apps/accounts/
**Forbidden Paths**: None

### Deliverables
- [ ] import_okvet_clients management command
- [ ] CSV/Excel parsing
- [ ] Duplicate detection
- [ ] User account creation
- [ ] Progress reporting
- [ ] Error logging

### Implementation Details

#### Management Command
```python
# apps/migration/management/commands/import_okvet_clients.py

class Command(BaseCommand):
    help = 'Import clients from OkVet.co export file'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Path to export file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate without importing'
        )
        parser.add_argument(
            '--skip-duplicates',
            action='store_true',
            help='Skip clients that already exist'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Records to process per batch'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        # Create migration batch
        batch = MigrationBatch.objects.create(
            source='okvet',
            source_file=file_path,
            dry_run=dry_run,
            started_by=None,  # Management command
            started_at=timezone.now()
        )

        try:
            self.import_clients(batch, file_path, options)
        except Exception as e:
            batch.status = 'failed'
            batch.save()
            raise

        batch.status = 'completed'
        batch.completed_at = timezone.now()
        batch.save()
```

#### Import Logic
```python
def import_clients(self, batch, file_path, options):
    """Process client import."""

    # Parse file
    if file_path.endswith('.csv'):
        data = self.parse_csv(file_path)
    elif file_path.endswith('.xlsx'):
        data = self.parse_excel(file_path)
    else:
        raise ValueError("Unsupported file format")

    batch.total_records = len(data)
    batch.save()

    for row in data:
        try:
            # Transform data
            client_data = self.transform_client(row)

            # Validate
            errors = MigrationValidator().validate_client(client_data)
            if errors:
                self.log_error(batch, row, errors)
                continue

            # Check for duplicates
            existing = self.find_duplicate(client_data)
            if existing:
                if options['skip_duplicates']:
                    self.log_skip(batch, row, 'Duplicate')
                    continue
                else:
                    # Update existing
                    self.update_client(existing, client_data, batch)
            else:
                # Create new
                self.create_client(client_data, batch)

            batch.processed_records += 1
            batch.save()

        except Exception as e:
            self.log_error(batch, row, str(e))

    self.print_summary(batch)
```

#### Duplicate Detection
```python
def find_duplicate(self, data: dict) -> User | None:
    """Find existing client by email or phone."""

    # Try email first
    if data.get('email'):
        existing = User.objects.filter(email__iexact=data['email']).first()
        if existing:
            return existing

    # Try phone
    if data.get('phone_number'):
        existing = User.objects.filter(
            phone_number=data['phone_number']
        ).first()
        if existing:
            return existing

    return None
```

#### Field Mapping (OkVet → Our System)
```python
OKVET_CLIENT_MAPPING = {
    'id_cliente': 'okvet_id',
    'nombre': 'first_name',
    'apellidos': 'last_name',
    'email': 'email',
    'telefono': 'phone_number',
    'celular': 'phone_number',  # Prefer mobile
    'direccion': 'address',
    'ciudad': 'city',
    'codigo_postal': 'postal_code',
    'notas': 'notes',
    'fecha_registro': 'date_joined',
}
```

### Usage Examples
```bash
# Dry run first
python manage.py import_okvet_clients clients.csv --dry-run

# Import with duplicate skip
python manage.py import_okvet_clients clients.csv --skip-duplicates

# Full import
python manage.py import_okvet_clients clients.csv
```

### Test Cases
- [ ] CSV parsing works
- [ ] Excel parsing works
- [ ] Field mapping correct
- [ ] Duplicates detected
- [ ] Duplicates skipped/updated
- [ ] New clients created
- [ ] Errors logged properly
- [ ] Dry run doesn't save
- [ ] Progress reported

### Definition of Done
- [ ] Command imports clients successfully
- [ ] All edge cases handled
- [ ] Comprehensive error logging
- [ ] Dry run mode works
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-018: Migration Models & Tracking

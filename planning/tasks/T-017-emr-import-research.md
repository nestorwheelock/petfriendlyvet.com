# T-017: Veterinary EMR Data Import

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Technical Analyst / Backend Developer
**Objective**: Design and implement generic data import from standard veterinary EMR export formats
**Related Story**: S-023
**Estimate**: 6 hours

### Constraints
**Allowed File Paths**: apps/core/management/commands/, apps/core/importers/, planning/research/
**Forbidden Paths**: None

### Overview

Instead of targeting a specific EMR system (OkVet.co), we will build a **generic import system** that handles common veterinary EMR export formats. This makes the system reusable for any clinic migrating from any EMR.

## Common Veterinary EMR Export Formats

Most veterinary practice management systems (PIMS) export data in these formats:

| Format | Systems | Handling |
|--------|---------|----------|
| **CSV** | Most systems | pandas, csv module |
| **Excel (.xlsx)** | Many systems | openpyxl, pandas |
| **JSON** | Modern systems | Built-in json |
| **XML** | Legacy systems | ElementTree |
| **SQL dump** | Some self-hosted | Custom parsing |

## Standard Data Categories

### Priority 1: Critical (Must import)
| Category | Typical Fields | Our Model |
|----------|---------------|-----------|
| **Clients/Owners** | name, phone, email, address | `accounts.User` + `crm.OwnerProfile` |
| **Pets** | name, species, breed, DOB, sex, weight | `pets.Pet` |
| **Vaccinations** | pet, vaccine_type, date, next_due, batch | `pets.Vaccination` |

### Priority 2: Important (Should import)
| Category | Typical Fields | Our Model |
|----------|---------------|-----------|
| **Medical Records** | pet, date, notes, diagnosis, treatment | `pets.MedicalRecord` |
| **Appointments (history)** | pet, date, service, notes, status | `appointments.Appointment` |

### Priority 3: Nice to Have (Can import later)
| Category | Typical Fields | Our Model |
|----------|---------------|-----------|
| **Invoices** | client, items, total, date, status | `billing.Invoice` |
| **Products/Inventory** | name, SKU, price, stock, category | `store.Product` |

## Deliverables
- [ ] Generic CSV importer base class
- [ ] Field mapping configuration system
- [ ] Data validation and cleaning utilities
- [ ] Import management commands
- [ ] Import status tracking model
- [ ] Rollback capability
- [ ] Import reports (success/errors)

## Implementation Details

### Base Importer Class
```python
# apps/core/importers/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import csv
import pandas as pd
from django.db import transaction

class BaseImporter(ABC):
    """Base class for all data importers."""

    # Override in subclass
    model = None
    field_mapping = {}  # {'source_field': 'model_field'}
    required_fields = []

    def __init__(self, file_path: str, dry_run: bool = False):
        self.file_path = file_path
        self.dry_run = dry_run
        self.errors = []
        self.warnings = []
        self.imported_count = 0
        self.skipped_count = 0

    def import_data(self) -> dict:
        """Run the full import process."""
        data = self.read_file()
        cleaned_data = self.clean_data(data)

        if self.dry_run:
            return self.validate_only(cleaned_data)

        with transaction.atomic():
            for row in cleaned_data:
                try:
                    self.import_row(row)
                    self.imported_count += 1
                except Exception as e:
                    self.errors.append({'row': row, 'error': str(e)})
                    self.skipped_count += 1

        return self.get_report()

    @abstractmethod
    def read_file(self) -> List[Dict]:
        """Read source file and return list of dicts."""
        pass

    def clean_data(self, data: List[Dict]) -> List[Dict]:
        """Clean and transform data."""
        cleaned = []
        for row in data:
            cleaned_row = {}
            for source_field, model_field in self.field_mapping.items():
                value = row.get(source_field, '')
                cleaned_row[model_field] = self.clean_field(model_field, value)
            cleaned.append(cleaned_row)
        return cleaned

    def clean_field(self, field_name: str, value: Any) -> Any:
        """Override for field-specific cleaning."""
        if isinstance(value, str):
            return value.strip()
        return value

    @abstractmethod
    def import_row(self, row: Dict) -> None:
        """Import a single row. Override in subclass."""
        pass

    def get_report(self) -> dict:
        return {
            'imported': self.imported_count,
            'skipped': self.skipped_count,
            'errors': self.errors,
            'warnings': self.warnings,
        }


class CSVImporter(BaseImporter):
    """Import from CSV files."""

    encoding = 'utf-8'
    delimiter = ','

    def read_file(self) -> List[Dict]:
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            return list(reader)


class ExcelImporter(BaseImporter):
    """Import from Excel files."""

    sheet_name = 0  # First sheet by default

    def read_file(self) -> List[Dict]:
        df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
        return df.to_dict('records')
```

### Client Importer Example
```python
# apps/core/importers/clients.py
from apps.accounts.models import User
from apps.crm.models import OwnerProfile
from .base import CSVImporter

class ClientImporter(CSVImporter):
    """Import client/owner records."""

    model = User

    # Map common EMR field names to our fields
    field_mapping = {
        # Spanish field names (common in Latin America)
        'nombre': 'first_name',
        'apellido': 'last_name',
        'telefono': 'phone_number',
        'correo': 'email',
        'email': 'email',  # English variant
        'direccion': 'address',

        # English field names
        'first_name': 'first_name',
        'last_name': 'last_name',
        'phone': 'phone_number',
        'address': 'address',

        # Generic
        'name': 'full_name',  # Will be split
    }

    required_fields = ['email']  # Or phone

    def clean_field(self, field_name: str, value):
        value = super().clean_field(field_name, value)

        if field_name == 'phone_number':
            return self.normalize_phone(value)
        if field_name == 'email':
            return value.lower() if value else None

        return value

    def normalize_phone(self, phone: str) -> str:
        """Normalize Mexican phone numbers."""
        if not phone:
            return ''
        # Remove non-digits
        digits = ''.join(c for c in phone if c.isdigit())
        # Add Mexico country code if needed
        if len(digits) == 10:
            return f'+52{digits}'
        if len(digits) == 12 and digits.startswith('52'):
            return f'+{digits}'
        return phone

    def import_row(self, row: dict):
        # Handle full_name split
        if 'full_name' in row and row['full_name']:
            parts = row['full_name'].split(' ', 1)
            row['first_name'] = parts[0]
            row['last_name'] = parts[1] if len(parts) > 1 else ''

        # Find or create user
        email = row.get('email')
        phone = row.get('phone_number')

        if email:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': row.get('first_name', ''),
                    'last_name': row.get('last_name', ''),
                    'phone_number': phone,
                }
            )
        elif phone:
            user, created = User.objects.get_or_create(
                phone_number=phone,
                defaults={
                    'first_name': row.get('first_name', ''),
                    'last_name': row.get('last_name', ''),
                }
            )
        else:
            raise ValueError("Client must have email or phone")

        # Create/update owner profile
        if row.get('address'):
            OwnerProfile.objects.update_or_create(
                user=user,
                defaults={'address': row['address']}
            )
```

### Management Command
```python
# apps/core/management/commands/import_data.py
from django.core.management.base import BaseCommand
from apps.core.importers.clients import ClientImporter
from apps.core.importers.pets import PetImporter
from apps.core.importers.vaccinations import VaccinationImporter

IMPORTERS = {
    'clients': ClientImporter,
    'pets': PetImporter,
    'vaccinations': VaccinationImporter,
}

class Command(BaseCommand):
    help = 'Import data from EMR export files'

    def add_arguments(self, parser):
        parser.add_argument('data_type', choices=IMPORTERS.keys())
        parser.add_argument('file_path', type=str)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--encoding', default='utf-8')

    def handle(self, *args, **options):
        importer_class = IMPORTERS[options['data_type']]
        importer = importer_class(
            file_path=options['file_path'],
            dry_run=options['dry_run']
        )

        self.stdout.write(f"Importing {options['data_type']}...")

        report = importer.import_data()

        self.stdout.write(self.style.SUCCESS(
            f"Imported: {report['imported']}, Skipped: {report['skipped']}"
        ))

        if report['errors']:
            self.stdout.write(self.style.WARNING(
                f"Errors: {len(report['errors'])}"
            ))
            for error in report['errors'][:5]:
                self.stdout.write(f"  - {error['error']}")
```

### Usage Examples

```bash
# Dry run to validate data
python manage.py import_data clients /path/to/clients.csv --dry-run

# Import clients
python manage.py import_data clients /path/to/clients.csv

# Import pets (requires clients first)
python manage.py import_data pets /path/to/pets.csv

# Import with different encoding
python manage.py import_data clients /path/to/clients.csv --encoding latin-1
```

## Import Status Tracking

```python
# apps/core/models.py
class ImportJob(models.Model):
    """Track import job status."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    data_type = models.CharField(max_length=50)  # clients, pets, etc.
    file_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    total_rows = models.IntegerField(default=0)
    imported_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)

    errors = models.JSONField(default=list)

    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Test Cases
- [ ] CSV import with standard fields
- [ ] CSV import with Spanish field names
- [ ] Excel import
- [ ] Dry run validation
- [ ] Duplicate handling (skip vs update)
- [ ] Invalid data handling
- [ ] Phone number normalization
- [ ] Email normalization
- [ ] Missing required fields
- [ ] Import rollback on error

## Acceptance Criteria

**AC-1: Generic CSV Import**
**Given** a CSV file with client data in any common format
**When** I run the import command
**Then** clients are created in the database with normalized data

**AC-2: Dry Run Validation**
**Given** a data file with some invalid records
**When** I run the import with --dry-run
**Then** I see a report of what would be imported and what errors exist

**AC-3: Duplicate Handling**
**Given** a client already exists with the same email
**When** I import a record with that email
**Then** the existing record is updated (not duplicated)

**AC-4: Import Tracking**
**Given** an import job is started
**When** the import completes
**Then** an ImportJob record shows the results and any errors

## Definition of Done
- [ ] Base importer class implemented
- [ ] Client importer working
- [ ] Pet importer working
- [ ] Vaccination importer working
- [ ] Management command functional
- [ ] Import tracking model created
- [ ] Tests written and passing (>95% coverage)
- [ ] Documentation for adding new importers

## Dependencies
- T-001: Django Project Setup
- T-003: Authentication (User model)
- T-024: Pet Models
- T-025: Medical Records Models

## Notes

This generic approach means:
1. We don't need to reverse-engineer OkVet.co's specific format
2. Any clinic can migrate from any EMR that exports CSV/Excel
3. Field mapping is configurable per import
4. Easy to extend for new EMR systems

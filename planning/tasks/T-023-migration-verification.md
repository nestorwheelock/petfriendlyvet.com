# T-023: Migration Verification

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement verification tools to validate migration accuracy
**Related Story**: S-023
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/migration/
**Forbidden Paths**: None

### Deliverables
- [ ] verify_migration management command
- [ ] Data integrity checks
- [ ] Comparison reports
- [ ] Missing data identification
- [ ] Statistics dashboard
- [ ] Export for review

### Implementation Details

#### Verification Command
```python
# apps/migration/management/commands/verify_migration.py

class Command(BaseCommand):
    help = 'Verify migration data integrity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['clients', 'pets', 'records', 'vaccinations', 'all'],
            default='all',
            help='Type of data to verify'
        )
        parser.add_argument(
            '--report',
            type=str,
            help='Output report file path'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix identified issues'
        )

    def handle(self, *args, **options):
        report = MigrationVerificationReport()

        if options['type'] in ['clients', 'all']:
            report.add_section(self.verify_clients())

        if options['type'] in ['pets', 'all']:
            report.add_section(self.verify_pets())

        if options['type'] in ['records', 'all']:
            report.add_section(self.verify_records())

        if options['type'] in ['vaccinations', 'all']:
            report.add_section(self.verify_vaccinations())

        report.add_section(self.verify_relationships())
        report.add_section(self.generate_statistics())

        if options['report']:
            report.export(options['report'])
        else:
            self.stdout.write(report.to_text())
```

#### Verification Checks
```python
def verify_clients(self) -> VerificationSection:
    """Verify client data integrity."""

    section = VerificationSection('Clients')

    # Check: All migration records have corresponding users
    orphaned = MigrationRecord.objects.filter(
        record_type='client',
        status='success'
    ).exclude(
        target_id__in=User.objects.values_list('id', flat=True)
    ).count()
    section.add_check('Orphaned records', orphaned == 0, f"{orphaned} orphaned")

    # Check: Required fields populated
    missing_email = User.objects.filter(
        email='',
        is_placeholder=False
    ).count()
    section.add_check('Missing emails', missing_email == 0, f"{missing_email} missing")

    # Check: Phone format valid
    invalid_phones = User.objects.filter(
        phone_number__regex=r'^(?!\+52)'
    ).exclude(phone_number='').count()
    section.add_check('Invalid phones', invalid_phones == 0, f"{invalid_phones} invalid")

    return section


def verify_pets(self) -> VerificationSection:
    """Verify pet data integrity."""

    section = VerificationSection('Pets')

    # Check: All pets have owners
    orphaned_pets = Pet.objects.filter(owner__isnull=True).count()
    section.add_check('Orphaned pets', orphaned_pets == 0, f"{orphaned_pets} orphaned")

    # Check: Species valid
    invalid_species = Pet.objects.exclude(
        species__in=['dog', 'cat', 'bird', 'rabbit', 'hamster', 'other']
    ).count()
    section.add_check('Invalid species', invalid_species == 0, f"{invalid_species} invalid")

    # Check: Birth dates reasonable
    future_births = Pet.objects.filter(birth_date__gt=timezone.now().date()).count()
    section.add_check('Future birth dates', future_births == 0, f"{future_births} future")

    return section


def verify_relationships(self) -> VerificationSection:
    """Verify data relationships."""

    section = VerificationSection('Relationships')

    # Check: Records link to existing pets
    orphan_records = MedicalRecord.objects.filter(pet__isnull=True).count()
    section.add_check('Orphan records', orphan_records == 0, f"{orphan_records} orphaned")

    # Check: Vaccinations link to existing pets
    orphan_vacc = Vaccination.objects.filter(pet__isnull=True).count()
    section.add_check('Orphan vaccinations', orphan_vacc == 0, f"{orphan_vacc} orphaned")

    return section
```

#### Statistics Generation
```python
def generate_statistics(self) -> VerificationSection:
    """Generate migration statistics."""

    section = VerificationSection('Statistics')

    stats = {
        'clients_imported': User.objects.filter(
            id__in=MigrationRecord.objects.filter(
                record_type='client', status='success'
            ).values_list('target_id', flat=True)
        ).count(),
        'pets_imported': Pet.objects.count(),
        'records_imported': MedicalRecord.objects.count(),
        'vaccinations_imported': Vaccination.objects.count(),
        'avg_pets_per_client': Pet.objects.count() / max(User.objects.count(), 1),
        'avg_records_per_pet': MedicalRecord.objects.count() / max(Pet.objects.count(), 1),
    }

    for key, value in stats.items():
        section.add_stat(key, value)

    return section
```

#### Report Format
```python
class MigrationVerificationReport:
    """Report generator for migration verification."""

    def to_text(self) -> str:
        """Generate text report."""
        lines = [
            "=" * 60,
            "MIGRATION VERIFICATION REPORT",
            f"Generated: {timezone.now()}",
            "=" * 60,
        ]

        for section in self.sections:
            lines.append(f"\n## {section.name}")
            lines.append("-" * 40)

            for check in section.checks:
                status = "✓" if check.passed else "✗"
                lines.append(f"  {status} {check.name}: {check.message}")

        return "\n".join(lines)

    def export(self, path: str):
        """Export report to file."""
        if path.endswith('.html'):
            self.export_html(path)
        elif path.endswith('.csv'):
            self.export_csv(path)
        else:
            with open(path, 'w') as f:
                f.write(self.to_text())
```

### Usage Examples
```bash
# Verify all data
python manage.py verify_migration

# Verify specific type with report
python manage.py verify_migration --type=pets --report=pet_verification.html

# Verify and attempt fixes
python manage.py verify_migration --fix
```

### Test Cases
- [ ] Verification identifies orphaned records
- [ ] Statistics accurate
- [ ] Report generates correctly
- [ ] HTML export works
- [ ] Fix mode repairs issues

### Definition of Done
- [ ] All verification checks implemented
- [ ] Report format clear
- [ ] Export options work
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-019: Client Import Command
- T-020: Pet Import Command
- T-021: Medical Records Import
- T-022: Vaccination Import

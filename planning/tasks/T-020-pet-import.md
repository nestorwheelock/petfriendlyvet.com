# T-020: Pet Import Command

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement management command to import pets from OkVet.co
**Related Story**: S-023
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/migration/, apps/vet_clinic/
**Forbidden Paths**: None

### Deliverables
- [ ] import_okvet_pets management command
- [ ] Owner linking
- [ ] Species/breed normalization
- [ ] Photo import (if available)
- [ ] Basic medical data

### Implementation Details

#### Management Command
```python
# apps/migration/management/commands/import_okvet_pets.py

class Command(BaseCommand):
    help = 'Import pets from OkVet.co export file'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Path to export file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate without importing'
        )
        parser.add_argument(
            '--require-owner',
            action='store_true',
            help='Skip pets without matching owner'
        )

    def handle(self, *args, **options):
        # Similar structure to client import
        pass
```

#### Pet Data Structure
```python
OKVET_PET_MAPPING = {
    'id_mascota': 'okvet_id',
    'id_cliente': 'owner_okvet_id',  # Link to owner
    'nombre': 'name',
    'especie': 'species',
    'raza': 'breed',
    'sexo': 'sex',
    'fecha_nacimiento': 'birth_date',
    'color': 'color',
    'peso': 'weight',
    'microchip': 'microchip_id',
    'esterilizado': 'is_neutered',
    'fallecido': 'is_deceased',
    'notas': 'notes',
    'foto': 'photo_url',
}
```

#### Species Normalization
```python
SPECIES_MAPPING = {
    # Spanish
    'perro': 'dog',
    'perra': 'dog',
    'can': 'dog',
    'gato': 'cat',
    'gata': 'cat',
    'felino': 'cat',
    'ave': 'bird',
    'pájaro': 'bird',
    'loro': 'bird',
    'conejo': 'rabbit',
    'hamster': 'hamster',
    'hámster': 'hamster',
    'tortuga': 'turtle',
    'pez': 'fish',
    'hurón': 'ferret',

    # English (if mixed)
    'dog': 'dog',
    'cat': 'cat',
    'bird': 'bird',
    'rabbit': 'rabbit',
}
```

#### Owner Linking
```python
def find_owner(self, okvet_owner_id: str) -> User | None:
    """Find owner by their OkVet ID stored during client import."""

    # Look up in migration records
    record = MigrationRecord.objects.filter(
        record_type='client',
        source_id=okvet_owner_id,
        status='success'
    ).first()

    if record:
        return User.objects.filter(id=record.target_id).first()

    return None


def handle_orphan_pet(self, pet_data: dict, options: dict):
    """Handle pet without matching owner."""

    if options['require_owner']:
        return None  # Skip

    # Create placeholder owner
    placeholder_email = f"unknown_{pet_data['okvet_id']}@placeholder.local"
    owner, created = User.objects.get_or_create(
        email=placeholder_email,
        defaults={
            'first_name': 'Propietario',
            'last_name': 'Desconocido',
            'is_active': False,  # Needs verification
        }
    )
    return owner
```

#### Photo Import
```python
async def import_photo(self, photo_url: str, pet: Pet) -> bool:
    """Download and attach photo if available."""

    if not photo_url or not photo_url.startswith('http'):
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_url) as response:
                if response.status == 200:
                    content = await response.read()
                    filename = f"pet_{pet.id}_{pet.name}.jpg"
                    pet.photo.save(filename, ContentFile(content))
                    return True
    except Exception as e:
        self.stderr.write(f"Photo import failed: {e}")

    return False
```

### Usage Examples
```bash
# Dry run
python manage.py import_okvet_pets pets.csv --dry-run

# Require owner match
python manage.py import_okvet_pets pets.csv --require-owner

# Full import (create placeholder owners)
python manage.py import_okvet_pets pets.csv
```

### Test Cases
- [ ] Pets import successfully
- [ ] Owner linking works
- [ ] Orphan pets handled
- [ ] Species normalized
- [ ] Breed preserved
- [ ] Photos downloaded
- [ ] Duplicates handled
- [ ] Errors logged

### Definition of Done
- [ ] Command imports pets successfully
- [ ] Owner relationships correct
- [ ] All species mapped
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-018: Migration Models & Tracking
- T-019: Client Import Command

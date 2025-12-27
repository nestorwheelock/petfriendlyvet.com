# T-021: Medical Records Import

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement management command to import medical records from OkVet.co
**Related Story**: S-023
**Estimate**: 6 hours

### Constraints
**Allowed File Paths**: apps/migration/, apps/vet_clinic/
**Forbidden Paths**: None

### Deliverables
- [ ] import_okvet_records management command
- [ ] Pet linking
- [ ] Record type classification
- [ ] SOAP note parsing
- [ ] Medication extraction
- [ ] Diagnosis mapping

### Implementation Details

#### Medical Record Types
```python
RECORD_TYPES = [
    ('consultation', 'Consulta'),
    ('surgery', 'Cirugía'),
    ('vaccination', 'Vacunación'),
    ('grooming', 'Estética'),
    ('lab_work', 'Laboratorio'),
    ('imaging', 'Imagenología'),
    ('dental', 'Dental'),
    ('emergency', 'Emergencia'),
    ('follow_up', 'Seguimiento'),
    ('other', 'Otro'),
]
```

#### Field Mapping
```python
OKVET_RECORD_MAPPING = {
    'id_historia': 'okvet_id',
    'id_mascota': 'pet_okvet_id',
    'fecha': 'date',
    'tipo': 'record_type',
    'motivo_consulta': 'chief_complaint',
    'sintomas': 'subjective',
    'examen_fisico': 'objective',
    'diagnostico': 'assessment',
    'tratamiento': 'plan',
    'notas': 'notes',
    'peso': 'weight',
    'temperatura': 'temperature',
    'frecuencia_cardiaca': 'heart_rate',
    'frecuencia_respiratoria': 'respiratory_rate',
    'veterinario': 'veterinarian_name',
    'costo': 'cost',
}
```

#### SOAP Note Parser
```python
class SOAPParser:
    """Parse unstructured notes into SOAP format."""

    def parse(self, text: str) -> dict:
        """Extract SOAP components from free text."""

        result = {
            'subjective': '',
            'objective': '',
            'assessment': '',
            'plan': ''
        }

        # Look for common patterns
        patterns = {
            'subjective': [
                r'(?:Motivo|Razón|Síntomas?):\s*(.+?)(?=\n|Examen|$)',
                r'(?:Chief complaint|CC):\s*(.+?)(?=\n|PE|$)',
            ],
            'objective': [
                r'(?:Examen físico|EF|PE):\s*(.+?)(?=\n|Diagnóstico|$)',
                r'(?:Physical exam):\s*(.+?)(?=\n|Dx|$)',
            ],
            'assessment': [
                r'(?:Diagnóstico|Dx):\s*(.+?)(?=\n|Tratamiento|$)',
                r'(?:Assessment|Diagnosis):\s*(.+?)(?=\n|Tx|$)',
            ],
            'plan': [
                r'(?:Tratamiento|Tx|Plan):\s*(.+?)(?=\n|$)',
                r'(?:Treatment|Rx):\s*(.+?)(?=\n|$)',
            ],
        }

        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    result[field] = match.group(1).strip()
                    break

        return result
```

#### Diagnosis Mapping
```python
# Common diagnosis codes for standardization
DIAGNOSIS_MAPPING = {
    # Spanish common diagnoses
    'parvovirus': 'K00001',
    'moquillo': 'K00002',
    'otitis': 'K00003',
    'dermatitis': 'K00004',
    'gastroenteritis': 'K00005',
    'fractura': 'K00006',
    'tumor': 'K00007',
    'diabetes': 'K00008',
    'insuficiencia renal': 'K00009',
    'artritis': 'K00010',
}
```

#### Medication Extraction
```python
def extract_medications(self, treatment_text: str) -> list[dict]:
    """Extract medication information from treatment text."""

    medications = []

    # Pattern: medication dose frequency duration
    pattern = r'(\w+(?:\s+\w+)?)\s+(\d+(?:\.\d+)?\s*(?:mg|ml|g|UI))\s+(?:cada|c/)\s*(\d+)\s*(?:h|hrs|horas)'

    for match in re.finditer(pattern, treatment_text, re.IGNORECASE):
        medications.append({
            'name': match.group(1),
            'dose': match.group(2),
            'frequency_hours': int(match.group(3)),
        })

    return medications
```

### Usage Examples
```bash
# Dry run
python manage.py import_okvet_records records.csv --dry-run

# Import with SOAP parsing
python manage.py import_okvet_records records.csv --parse-soap

# Full import
python manage.py import_okvet_records records.csv
```

### Test Cases
- [ ] Records import successfully
- [ ] Pet linking works
- [ ] SOAP parsing extracts data
- [ ] Medications extracted
- [ ] Diagnoses mapped
- [ ] Vital signs preserved
- [ ] Dates parsed correctly
- [ ] Cost data imported

### Definition of Done
- [ ] All medical records importable
- [ ] SOAP notes structured
- [ ] Vital signs preserved
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-018: Migration Models & Tracking
- T-020: Pet Import Command

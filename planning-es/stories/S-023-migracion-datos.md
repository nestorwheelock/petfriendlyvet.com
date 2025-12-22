# S-023: Migración de Datos (Importación de OkVet.co)

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** CRÍTICA
**Época:** 1 (Fundación)
**Estado:** PENDIENTE
**Módulo:** Comandos de gestión + scripts únicos

## Historia de Usuario

**Como** dueño de clínica
**Quiero** migrar todos los datos existentes de OkVet.co
**Para** no perder años de registros de clientes y pacientes

**Como** dueño de mascota
**Quiero** ver el historial completo de mi mascota en el nuevo sistema
**Para** tener continuidad de registros de cuidado

**Como** veterinario
**Quiero** acceder a registros médicos históricos
**Para** poder proporcionar cuidado informado basado en el historial de la mascota

## Importancia Crítica

**Esta es la historia MÁS CRÍTICA para la preparación del lanzamiento.**

El Dr. Pablo tiene años de datos en OkVet.co:
- Registros de clientes/dueños
- Perfiles de mascotas e historiales médicos
- Registros de vacunación
- Historial de citas
- Historial de facturas/facturación

**Sin una migración exitosa, el nuevo sistema no puede lanzarse.**

## Criterios de Aceptación

### Exportación de Datos desde OkVet.co
- [ ] Investigar opciones de exportación de OkVet.co (CSV, API, manual)
- [ ] Documentar estructura de datos de OkVet.co
- [ ] Obtener archivos de exportación de muestra del Dr. Pablo
- [ ] Identificar todos los tipos de datos exportables
- [ ] Documentar cualquier dato que no se pueda exportar

### Mapeo de Datos
- [ ] Mapear campos de OkVet.co a nuestros modelos
- [ ] Identificar transformaciones requeridas
- [ ] Documentar conversiones de tipos de datos
- [ ] Planear campos faltantes/opcionales
- [ ] Manejar diferencias de formato de fecha/hora

### Datos a Migrar

| Tipo de Datos | Prioridad | Origen | Destino |
|-----------|----------|--------|-------------|
| Clientes/Dueños | Crítica | Clientes OkVet | User + OwnerProfile |
| Mascotas | Crítica | Pacientes OkVet | Modelo Pet |
| Historial Médico | Crítica | Registros OkVet | MedicalRecord |
| Vacunaciones | Crítica | Vacunas OkVet | VaccinationRecord |
| Citas | Alta | Agenda OkVet | Appointment (histórico) |
| Facturas | Alta | Facturación OkVet | Invoice (histórico) |
| Productos | Media | Inventario OkVet | Product |
| Documentos/Fotos | Media | Adjuntos OkVet | Document/Media |

### Proceso de Migración
- [ ] Scripts de validación y limpieza de datos
- [ ] Detección y manejo de duplicados
- [ ] Scripts de transformación de datos
- [ ] Scripts de importación con capacidad de reversión
- [ ] Reportes de progreso durante importación
- [ ] Registro de errores y reportes
- [ ] Modo de prueba para testing

### Integridad de Datos
- [ ] Mantener integridad referencial (dueño → mascota → registros)
- [ ] Preservar IDs originales como external_id para referencia
- [ ] Manejar registros huérfanos con gracia
- [ ] Validar campos requeridos
- [ ] Registrar todos los problemas de calidad de datos

### Verificación Post-Migración
- [ ] Verificación de conteo de registros (origen vs destino)
- [ ] Verificación aleatoria de registros
- [ ] Verificar relaciones mantenidas
- [ ] Reportes de comparación lado a lado
- [ ] Identificación de datos faltantes
- [ ] Herramientas de corrección manual

## Requisitos Técnicos

### Modelos (Soporte de Migración)

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

### Comandos de Gestión

```python
# Ejemplos de uso:

# 1. Validar datos de origen (prueba)
python manage.py import_okvet_clients --file=clients.csv --dry-run

# 2. Importar con capacidad de reversión
python manage.py import_okvet_clients --file=clients.csv

# 3. Importar mascotas (requiere clientes primero)
python manage.py import_okvet_pets --file=pets.csv

# 4. Importar registros médicos (requiere mascotas)
python manage.py import_okvet_records --file=medical_history.csv

# 5. Importar vacunaciones
python manage.py import_okvet_vaccines --file=vaccines.csv

# 6. Verificar migración
python manage.py verify_migration --report=migration_report.html

# 7. Revertir si es necesario
python manage.py rollback_migration --batch-id=123

# 8. Generar reporte de comparación
python manage.py compare_migration --output=comparison.html
```

### Patrón de Implementación de Comandos

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

### Referencia de Mapeo de Campos

```python
# Mapeos de campos esperados de OkVet.co (a confirmar con exportación real)

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

## Fases de Migración

### Fase 1: Investigación y Preparación
1. Contactar soporte de OkVet.co sobre opciones de exportación
2. Obtener exportaciones de muestra del Dr. Pablo
3. Documentar estructura de datos real
4. Identificar volumen de datos (conteos de registros)
5. Planear cronograma de migración

### Fase 2: Desarrollo
1. Construir comandos de importación
2. Construir reglas de validación
3. Construir detección de duplicados
4. Construir mecanismo de reversión
5. Crear modo de prueba

### Fase 3: Pruebas
1. Importar en entorno de desarrollo
2. Ejecutar validación completa
3. Arreglar problemas de calidad de datos
4. Verificar conteos de registros
5. Probar todos los tipos de registros

### Fase 4: Migración en Producción
1. Programar ventana de tiempo de inactividad
2. Exportación final de OkVet.co
3. Ejecutar importación en producción
4. Verificar integridad
5. Habilitar nuevo sistema

### Fase 5: Verificación
1. Comparación lado a lado
2. Verificaciones aleatorias
3. Pruebas de aceptación de usuario
4. Arreglar cualquier problema encontrado
5. Aprobación del Dr. Pablo

## Reportes de Verificación

### Reporte de Conteo de Registros
```
═══════════════════════════════════════
REPORTE DE VERIFICACIÓN DE MIGRACIÓN
═══════════════════════════════════════
Fecha: [Fecha]
Origen: OkVet.co
Destino: Pet-Friendly v1.0

CONTEOS DE REGISTROS:
                    Origen    Importados   Diff
Clientes/Dueños:     1,234     1,230       -4*
Mascotas:            2,456     2,450       -6*
Registros Médicos:  12,345    12,340       -5*
Vacunaciones:        5,678     5,678        0
Citas:               8,901     8,901        0
Facturas:            6,789     6,785       -4*

* Ver problemas de calidad de datos para detalles

PROBLEMAS DE CALIDAD DE DATOS:
- 4 clientes sin información de contacto válida (omitidos)
- 6 mascotas con referencias de dueño huérfanas (marcadas)
- 5 registros médicos con errores de formato de fecha (corregidos)

LISTA DE VERIFICACIÓN:
✅ Todos los clientes con datos válidos importados
✅ Todas las mascotas vinculadas a dueños correctos
✅ Historial médico completo para todas las mascotas
✅ Registros de vacunación actuales
✅ Historial de facturas preservado

APROBACIÓN:
□ Datos verificados por: ________________
□ Fecha: ________________
═══════════════════════════════════════
```

## Definición de Terminado

- [ ] Formato de exportación de OkVet.co documentado
- [ ] Todos los comandos de importación creados
- [ ] Modo de validación de prueba funcionando
- [ ] Capacidad de reversión implementada
- [ ] Detección de duplicados funcionando
- [ ] Mapeo de ID externo preservado
- [ ] Todos los tipos de datos importados exitosamente
- [ ] Reportes de verificación generados
- [ ] Problemas de calidad de datos registrados y resueltos
- [ ] Aprobación del Dr. Pablo sobre datos migrados
- [ ] Pruebas escritas y pasando (>95% cobertura)

## Dependencias

- S-001: Fundación (los modelos deben existir)
- S-003: Perfiles de Mascotas (modelo Pet)
- S-007: CRM (OwnerProfile)

## Investigación Necesaria

1. **Opciones de Exportación de OkVet.co**
   - ¿OkVet.co proporciona exportación CSV/Excel?
   - ¿Hay una API para extracción de datos?
   - ¿Cuáles son las limitaciones de exportación?
   - Contacto: support@okvet.co

2. **Volumen de Datos**
   - ¿Cuántos clientes en OkVet.co?
   - ¿Cuántas mascotas?
   - ¿Cuántos registros médicos?
   - ¿Cuántos años de historial?

3. **Calidad de Datos**
   - Inspección de datos de muestra
   - Problemas comunes de calidad de datos
   - Campos requeridos faltantes

## Riesgos

| Riesgo | Impacto | Mitigación |
|------|--------|------------|
| OkVet.co no soporta exportación | Alto | Entrada manual, scraping de pantalla |
| Formato de datos inesperado | Medio | Analizadores flexibles, mapeo manual |
| Datos duplicados/inconsistentes | Medio | Reglas de deduplicación, revisión manual |
| Datos históricos faltantes | Alto | Enfoque por fases, migración parcial |
| Ventana de migración muy pequeña | Medio | Migración fuera de horario, sincronización incremental |

## Notas

- **ESTO DEBE COMPLETARSE ANTES DEL LANZAMIENTO**
- Iniciar investigación inmediatamente después de aprobación del proyecto
- Obtener exportaciones de muestra del Dr. Pablo ASAP
- Planear al menos 2 migraciones de prueba completas antes de producción
- Considerar período de ejecución paralela (ambos sistemas activos)
- Mantener OkVet.co accesible como referencia durante la transición

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.

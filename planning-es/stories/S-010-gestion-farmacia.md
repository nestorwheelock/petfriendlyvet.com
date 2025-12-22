# S-010: Gestión de Farmacia

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Alta
**Época:** 3 (con E-Commerce)
**Estado:** PENDIENTE
**Módulo:** django-simple-store (extensión de farmacia)

## Historia de Usuario

**Como** dueño de mascota
**Quiero** ordenar medicamentos recetados y solicitar resurtidos en línea
**Para que** pueda gestionar convenientemente las necesidades de medicación de mi mascota

**Como** veterinario
**Quiero** gestionar recetas y rastrear sustancias controladas
**Para que** mantenga el cumplimiento y proporcione gestión segura de medicamentos

**Como** miembro del personal de farmacia
**Quiero** procesar órdenes de recetas y gestionar inventario
**Para que** pueda cumplir eficientemente las solicitudes de medicamentos

## Criterios de Aceptación

### Gestión de Recetas
- [ ] Crear recetas vinculadas a mascota y visita
- [ ] La receta incluye medicamento, dosis, frecuencia, duración
- [ ] La receta tiene conteo de resurtidos y fecha de expiración
- [ ] Rastrear estado de receta (activa, expirada, cancelada)
- [ ] La receta requiere autorización del veterinario
- [ ] Vincular recetas a citas/visitas

### Solicitudes de Resurtido
- [ ] Los dueños pueden solicitar resurtidos vía chat de IA
- [ ] El sistema verifica resurtidos restantes y expiración
- [ ] Negación automática si no hay resurtidos o está expirada
- [ ] Notificar al veterinario para autorización si es necesario
- [ ] Historial de resurtidos rastreado por receta
- [ ] Recordar a dueños cuando vencen resurtidos

### Sustancias Controladas
- [ ] Marcar medicamentos controlados (Lista II-V)
- [ ] Requerir verificación adicional para sustancias controladas
- [ ] Registro e informes compatibles con DEA
- [ ] No se pueden resurtir sustancias controladas en línea (solo recoger)
- [ ] Rastrear dispensación por miembro del personal
- [ ] Rastro de auditoría para todas las transacciones de sustancias controladas

### Base de Datos de Medicamentos
- [ ] Base de datos completa de medicamentos
- [ ] Verificación de interacciones medicamentosas
- [ ] Guías de dosificación específicas por especie
- [ ] Contraindicaciones y advertencias
- [ ] Mapeo de nombres genéricos/marca
- [ ] Rastreo de fabricante y NDC

### Inventario de Farmacia
- [ ] Rastrear niveles de stock de medicamentos
- [ ] Rastreo de número de lote y caducidad
- [ ] Alertas automáticas de reorden
- [ ] Vincular inventario a recetas surtidas
- [ ] Registro de desperdicios y ajustes
- [ ] Gestión de proveedores

### Cumplimiento de Órdenes
- [ ] Cola para órdenes de recetas pendientes
- [ ] Paso de verificación del farmacéutico
- [ ] Impresión de etiquetas con instrucciones
- [ ] Opciones de recoger vs entrega
- [ ] Notificación cuando está lista para recoger
- [ ] Integración de pago con checkout de tienda

## Requisitos Técnicos

### Modelos

```python
class Medication(models.Model):
    """Drug/medication reference database"""
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_names = models.JSONField(default=list)
    ndc = models.CharField(max_length=20, blank=True)  # National Drug Code

    # Classification
    drug_class = models.CharField(max_length=100)
    schedule = models.CharField(max_length=10, blank=True)  # II, III, IV, V or blank
    is_controlled = models.BooleanField(default=False)
    requires_prescription = models.BooleanField(default=True)

    # Dosing
    species = models.JSONField(default=list)  # ["dog", "cat", "bird", ...]
    dosage_forms = models.JSONField(default=list)  # tablet, liquid, injection
    strengths = models.JSONField(default=list)  # ["10mg", "25mg", "50mg"]
    default_dosing = models.JSONField(default=dict)  # Per species guidelines

    # Safety
    contraindications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    drug_interactions = models.JSONField(default=list)  # List of interacting drug IDs
    warnings = models.TextField(blank=True)

    # Metadata
    manufacturer = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']


class Prescription(models.Model):
    """Prescription issued to a pet"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),  # All refills used
    ]

    # References
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    prescribing_vet = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True
    )
    visit = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Medication details
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)
    strength = models.CharField(max_length=50)
    dosage_form = models.CharField(max_length=50)  # tablet, capsule, liquid
    quantity = models.IntegerField()

    # Instructions
    dosage = models.CharField(max_length=100)  # "1 tablet"
    frequency = models.CharField(max_length=100)  # "twice daily"
    duration = models.CharField(max_length=100)  # "14 days"
    instructions = models.TextField(blank=True)  # "Give with food"

    # Refills
    refills_authorized = models.IntegerField(default=0)
    refills_remaining = models.IntegerField(default=0)

    # Validity
    prescribed_date = models.DateField()
    expiration_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # For controlled substances
    dea_number = models.CharField(max_length=20, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-prescribed_date']


class PrescriptionFill(models.Model):
    """Record of each time a prescription is filled"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)

    # Fill details
    fill_number = models.IntegerField()  # 0 = original, 1+ = refills
    quantity_dispensed = models.IntegerField()

    # Inventory tracking
    lot_number = models.CharField(max_length=50, blank=True)
    expiration_date = models.DateField(null=True)

    # Staff
    dispensed_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True
    )
    verified_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True,
        related_name='verified_fills'
    )

    # Order reference
    order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Status
    status = models.CharField(max_length=20, default='pending')
    # pending, processing, ready, picked_up, delivered, cancelled

    # Pickup/delivery
    fulfillment_method = models.CharField(max_length=20)  # pickup, delivery
    ready_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-requested_at']


class RefillRequest(models.Model):
    """Pet owner request for prescription refill"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Request details
    quantity_requested = models.IntegerField(null=True)  # null = standard quantity
    notes = models.TextField(blank=True)

    # Processing
    status = models.CharField(max_length=20, default='pending')
    # pending, approved, denied, filled

    # Authorization (if needed)
    requires_authorization = models.BooleanField(default=False)
    authorized_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True, blank=True
    )
    authorized_at = models.DateTimeField(null=True)
    denial_reason = models.TextField(blank=True)

    # Result
    fill = models.ForeignKey(
        PrescriptionFill, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ControlledSubstanceLog(models.Model):
    """DEA-compliant log for controlled substances"""
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT)

    # Transaction
    transaction_type = models.CharField(max_length=20)
    # received, dispensed, wasted, returned, adjusted
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)  # tablets, ml, etc.

    # Running balance
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)

    # References
    prescription_fill = models.ForeignKey(
        PrescriptionFill, on_delete=models.SET_NULL, null=True, blank=True
    )
    lot_number = models.CharField(max_length=50, blank=True)

    # Staff
    performed_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.PROTECT
    )
    witnessed_by = models.ForeignKey(
        'practice.StaffProfile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='witnessed_logs'
    )

    # Notes
    notes = models.TextField(blank=True)

    # Immutable timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        # This table should be append-only for compliance


class DrugInteraction(models.Model):
    """Drug-drug interaction warnings"""
    medication_1 = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name='interactions_as_primary'
    )
    medication_2 = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name='interactions_as_secondary'
    )

    severity = models.CharField(max_length=20)  # major, moderate, minor
    description = models.TextField()
    clinical_effects = models.TextField(blank=True)
    management = models.TextField(blank=True)

    class Meta:
        unique_together = ['medication_1', 'medication_2']
```

### Herramientas de IA

```python
PHARMACY_TOOLS = [
    {
        "name": "get_pet_prescriptions",
        "description": "Get active prescriptions for a pet",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "include_expired": {"type": "boolean", "default": False}
            },
            "required": ["pet_id"]
        }
    },
    {
        "name": "request_refill",
        "description": "Request a prescription refill",
        "parameters": {
            "type": "object",
            "properties": {
                "prescription_id": {"type": "integer"},
                "quantity": {"type": "integer"},
                "notes": {"type": "string"}
            },
            "required": ["prescription_id"]
        }
    },
    {
        "name": "check_refill_eligibility",
        "description": "Check if a prescription can be refilled",
        "parameters": {
            "type": "object",
            "properties": {
                "prescription_id": {"type": "integer"}
            },
            "required": ["prescription_id"]
        }
    },
    {
        "name": "get_medication_info",
        "description": "Get information about a medication",
        "parameters": {
            "type": "object",
            "properties": {
                "medication_name": {"type": "string"},
                "species": {"type": "string"}
            },
            "required": ["medication_name"]
        }
    },
    {
        "name": "check_drug_interactions",
        "description": "Check for drug interactions with pet's current medications",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "new_medication_id": {"type": "integer"}
            },
            "required": ["pet_id", "new_medication_id"]
        }
    },
    {
        "name": "get_refill_status",
        "description": "Check status of a refill request",
        "parameters": {
            "type": "object",
            "properties": {
                "refill_request_id": {"type": "integer"}
            },
            "required": ["refill_request_id"]
        }
    },
    {
        "name": "create_prescription",
        "description": "Create a new prescription (vet only)",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_id": {"type": "integer"},
                "medication_id": {"type": "integer"},
                "strength": {"type": "string"},
                "quantity": {"type": "integer"},
                "dosage": {"type": "string"},
                "frequency": {"type": "string"},
                "duration": {"type": "string"},
                "refills": {"type": "integer"},
                "instructions": {"type": "string"}
            },
            "required": ["pet_id", "medication_id", "quantity", "dosage", "frequency"]
        }
    },
    {
        "name": "get_pharmacy_queue",
        "description": "Get pending prescription orders (staff only)",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pending", "processing", "ready"]}
            }
        }
    }
]
```

## Ejemplo de Conversaciones con IA

### Solicitud de Resurtido (Cliente)
```
Dueño: Luna necesita más de su medicamento para tiroides

IA: ¡Puedo ayudarte con eso! Déjame revisar las recetas de Luna.

    Luna tiene una receta activa:
    - Metimazol tabletas 5mg
    - Recetado: 15 Nov 2025
    - Resurtidos restantes: 2 de 3
    - Expira: 15 May 2026

    ¿Te gustaría que solicite un resurtido?

Dueño: Sí por favor

IA: Resurtido solicitado para Metimazol 5mg de Luna.

    Detalles de la Orden:
    - Cantidad: 60 tabletas (suministro 30 días)
    - Recoger: Farmacia Pet-Friendly
    - Listo estimado: Hoy a las 4:00 PM

    Te enviaremos una notificación cuando esté listo.
    El costo será $285 MXN.

    ¿Te gustaría pagar ahora o cuando recojas?
```

### Advertencia de Interacción Medicamentosa (Veterinario)
```
Dr. Pablo: Recetar tramadol para Max

IA: Antes de crear esta receta, necesito alertarte
    sobre una posible interacción medicamentosa:

    ⚠️ INTERACCIÓN MODERADA

    Max está actualmente tomando:
    - Fluoxetina (Prozac) 20mg diario

    Tramadol + Fluoxetina pueden aumentar el riesgo de
    síndrome serotoninérgico.

    Efectos Clínicos:
    - Agitación, temblores, hipertermia
    - En casos severos: convulsiones

    Opciones de Manejo:
    1. Usar medicamento alternativo para dolor (gabapentina)
    2. Proceder con monitoreo cercano
    3. Reducir dosis de fluoxetina temporalmente

    ¿Cómo te gustaría proceder?
```

### Sustancia Controlada (Personal)
```
Personal: Dispensar ketamina para preparación de cirugía

IA: Esta es una sustancia controlada Lista III.
    Necesito registrar esta transacción.

    Inventario Actual:
    - Ketamina 100mg/ml, viales 10ml
    - Balance: 5 viales (50ml total)

    Por favor confirma:
    - Cantidad a dispensar: ___
    - Paciente/Propósito: ___
    - Testigo presente: ___

Personal: 2ml para cirugía dental de Max, testificado por Dr. Pablo

IA: Sustancia controlada registrada:

    Transacción: Dispensado 2ml Ketamina
    Paciente: Max (cirugía dental)
    Dispensado por: [Nombre del personal]
    Testificado por: Dr. Pablo
    Balance: 48ml restantes

    Registro DEA actualizado. Recibo impreso.
```

## Requisitos de Cumplimiento

### Cumplimiento DEA (Sustancias Controladas)
- Mantener registros de inventario precisos
- Registrar todas las transacciones con testigo para Lista II
- Requisitos de almacenamiento seguro
- Inventario bianual requerido
- Reportar discrepancias inmediatamente
- El personal debe tener credenciales válidas

### Regulaciones de México (COFEPRIS)
- Requisitos de receta para sustancias controladas
- Requisitos de retención de registros (5 años)
- Requisitos de reporte para psicotrópicos
- Requisitos de etiquetado apropiado

## Definición de Completado

- [ ] Base de datos de medicamentos con 500+ medicamentos veterinarios comunes
- [ ] Modelo de receta con ciclo de vida completo
- [ ] Flujo de trabajo de solicitud de resurtido
- [ ] Verificación de interacciones medicamentosas
- [ ] Registro de sustancias controladas (compatible con DEA)
- [ ] Cola de farmacia para personal
- [ ] Integración con checkout de e-commerce
- [ ] Notificación cuando está listo para recoger
- [ ] Herramientas de IA para cliente y personal
- [ ] Impresión de etiquetas de receta
- [ ] Pruebas escritas y pasando (>95% cobertura)

## Dependencias

- S-003: Perfiles de Mascotas (referencia de mascota)
- S-004: Citas (referencia de visita)
- S-005: E-Commerce (integración de orden)
- S-008: Gestión de Práctica (perfiles de personal)

## Notas

- Considerar importar base de datos de medicamentos desde fuentes FDA/veterinarias
- Puede necesitar almacenamiento separado de sustancias controladas en BD
- Impresión de etiquetas requiere integración de impresora térmica
- Las regulaciones COFEPRIS pueden diferir de DEA - investigación necesaria

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.

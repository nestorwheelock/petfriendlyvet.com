# S-008: Gestión de Práctica

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Baja
**Época:** 6
**Estado:** PENDIENTE

## Historia de Usuario

**Como** dueño de clínica
**Quiero** gestionar horarios del personal y operaciones internas
**Para que** la clínica funcione eficientemente

**Como** oficial de cumplimiento regulatorio
**Quiero** acceder a registros de auditoría y generar reportes de cumplimiento
**Para que** la clínica cumpla con los requisitos legales

## Criterios de Aceptación

### Gestión de Personal
- [ ] Perfiles de personal con roles y permisos
- [ ] Gestión de horarios de trabajo
- [ ] Solicitudes y aprobaciones de tiempo libre
- [ ] Disponibilidad del personal reflejada en reservas

### Notas Clínicas Internas
- [ ] Notas visibles solo para personal clínico
- [ ] Vinculadas a visitas y mascotas
- [ ] Buscables y filtrables
- [ ] Plantillas para tipos comunes de notas

### Gestión de Inventario
- [ ] Niveles de stock rastreados
- [ ] Alertas de stock bajo
- [ ] Sugerencias de reorden
- [ ] Seguimiento de fechas de caducidad
- [ ] Uso vinculado a visitas/ventas

### Cumplimiento y Auditoría
- [ ] Registro de auditoría inmutable para todas las acciones
- [ ] Registros exportables para inspecciones
- [ ] Políticas de retención configurables
- [ ] Soporte para exportación/eliminación de datos GDPR

### Reportes
- [ ] Resúmenes diarios/semanales/mensuales
- [ ] Reportes de ingresos
- [ ] Reportes de utilización de servicios
- [ ] Reportes de inventario
- [ ] Productividad del personal (opcional)

## Requisitos Técnicos

### Modelos

```python
# Staff Management
class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # veterinarian, assistant, receptionist, admin
    hire_date = models.DateField()
    license_number = models.CharField(max_length=50, blank=True)
    specializations = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)


class WorkSchedule(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    day_of_week = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)


class TimeOffRequest(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='pending')
    approved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


# Audit Logging
class AuditLog(models.Model):
    """Immutable audit log for compliance"""
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)  # create, update, delete, view
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict)  # Before/after for updates
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        # Prevent deletion/modification
        managed = True


# Inventory (extension of store.Product)
class InventoryMovement(models.Model):
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20)  # sale, restock, adjustment, expired
    quantity = models.IntegerField()  # Positive for in, negative for out
    reference = models.CharField(max_length=100, blank=True)  # Order ID, visit ID, etc.
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class InventoryAlert(models.Model):
    product = models.ForeignKey('store.Product', on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20)  # low_stock, expiring, out_of_stock
    threshold = models.IntegerField(null=True)
    expiry_date = models.DateField(null=True)
    is_active = models.BooleanField(default=True)
    acknowledged_at = models.DateTimeField(null=True)


# Compliance
class DataRetentionPolicy(models.Model):
    model_name = models.CharField(max_length=100)
    retention_days = models.IntegerField()
    action = models.CharField(max_length=20)  # delete, anonymize, archive
    is_active = models.BooleanField(default=True)


class DataExportRequest(models.Model):
    """GDPR data export/deletion requests"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=20)  # export, delete
    status = models.CharField(max_length=20, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    export_file = models.FileField(upload_to='exports/', null=True)
```

### Herramientas de IA (Época 6)

```python
PRACTICE_MANAGEMENT_TOOLS = [
    {
        "name": "get_staff_schedule",
        "description": "Get staff work schedule for a date",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"},
                "staff_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_inventory_status",
        "description": "Get current inventory status and alerts",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "show_alerts_only": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "record_inventory_adjustment",
        "description": "Record an inventory adjustment",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "quantity": {"type": "integer"},
                "reason": {"type": "string"}
            },
            "required": ["product_id", "quantity", "reason"]
        }
    },
    {
        "name": "get_audit_log",
        "description": "Search audit logs",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "action": {"type": "string"},
                "model": {"type": "string"},
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"}
            }
        }
    },
    {
        "name": "generate_compliance_report",
        "description": "Generate compliance/regulatory reports",
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": ["audit_summary", "data_access", "medical_records", "inventory"]
                },
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "format": {"type": "string", "enum": ["pdf", "csv", "json"]}
            },
            "required": ["report_type"]
        }
    },
    {
        "name": "get_daily_summary",
        "description": "Get daily business summary",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "format": "date"}
            }
        }
    }
]
```

## Ejemplo de Conversaciones con IA

### Resumen Diario
```
Dr. Pablo: ¿Cómo nos fue hoy?
IA: Aquí está el resumen de hoy (20 de diciembre de 2025):

    📊 **Resumen Diario**

    💰 **Ingresos:** $8,450 MXN
    • Servicios: $4,200 MXN (6 citas)
    • Productos: $4,250 MXN (8 órdenes)

    📅 **Citas:**
    • Completadas: 6 de 7 (1 ausencia)
    • Servicios: 3 chequeos, 2 vacunaciones, 1 cirugía

    🛒 **Productos Más Vendidos:**
    • Royal Canin (3 bolsas)
    • Frontline Plus (4 unidades)
    • Juguetes para perros (5 artículos)

    ⚠️ **Alertas:**
    • Stock bajo: Frontline Plus (2 restantes)
    • Por caducar pronto: Lote de vacuna antirrábica (caduca 15 Ene)

    Comparado con el viernes pasado: Ingresos arriba 12%
```

### Alerta de Inventario
```
IA: ⚠️ Alerta de Inventario

    Los siguientes artículos necesitan atención:

    🔴 **Agotado:**
    • Hills Prescription Diet k/d

    🟡 **Stock Bajo (reorden recomendado):**
    • Frontline Plus Perro Grande (2 restantes, umbral: 5)
    • Royal Canin Gastrointestinal (3 restantes, umbral: 5)

    🟠 **Caduca en 30 Días:**
    • Lote de Vacuna Antirrábica #R2024-15 (8 dosis, caduca 15 Ene)
    • Lote de Ketamina #K2024-08 (caduca 20 Ene)

    ¿Te gustaría que creara una lista de reorden?
```

## Definición de Completado

- [ ] Horarios de personal gestionables
- [ ] Solicitudes de tiempo libre funcionando
- [ ] Registro de auditoría capturando todas las acciones
- [ ] Registros de auditoría inmutables y exportables
- [ ] Movimientos de inventario rastreados
- [ ] Alertas de stock bajo y caducidad funcionando
- [ ] Reporte de resumen diario disponible
- [ ] Exportación/eliminación GDPR implementada
- [ ] La IA puede consultar todos los datos de la práctica
- [ ] Pruebas escritas y pasando (>95% cobertura)

## Dependencias

- Todas las épocas anteriores (S-001 hasta S-007)
- Sistema completo operacional

## Notas

- Los registros de auditoría deben ser verdaderamente inmutables (considerar tabla solo-agregar)
- Cumplimiento GDPR importante para turistas europeos
- Integración con OkVet.co por determinar (puede requerir investigación)
- Considerar base de datos de cumplimiento separada para retención a largo plazo

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.

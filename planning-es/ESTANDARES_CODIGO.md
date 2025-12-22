# Estándares de Código y Reglas

**IMPORTANTE:** Todas las tareas e historias de usuario DEBEN seguir estos estándares. Revise este documento antes de comenzar cualquier trabajo de implementación.

---

## Lista de Verificación Rápida

Antes de escribir CUALQUIER código, verifique:

- [ ] **TDD**: ¿Escribiendo prueba PRIMERO? (Rojo → Verde → Refactorizar)
- [ ] **Arquitectura**: ¿Código en ubicación correcta? (packages/ vs apps/website/)
- [ ] **Importaciones**: ¿Usando `apps.get_model()` para modelos entre paquetes?
- [ ] **Servicios**: ¿API pública en `services.py`, sin acceso directo a modelos?
- [ ] **Pruebas**: ¿Objetivo de cobertura >95%?

---

## 1. Reglas de Desarrollo Guiado por Pruebas (TDD)

### El Ciclo TDD (OBLIGATORIO)

```
1. ROJO    → Escribir una prueba que falle primero
2. VERDE   → Escribir código mínimo para pasar la prueba
3. REFACTORIZAR → Limpiar manteniendo las pruebas verdes
4. REPETIR
```

### Cumplimiento de TDD

**NUNCA escriba código de implementación antes de las pruebas.**

```python
# ORDEN CORRECTO:
# 1. Escribir prueba
def test_appointment_can_be_created():
    appointment = Appointment.objects.create(...)
    assert appointment.id is not None

# 2. Ejecutar prueba - FALLA (Rojo)
# 3. Escribir código mínimo para pasar
# 4. Ejecutar prueba - PASA (Verde)
# 5. Refactorizar si es necesario
```

### Requisitos de Cobertura de Pruebas

| Tipo | Cobertura Mínima |
|------|------------------|
| Modelos | 95% |
| Vistas | 95% |
| Servicios | 95% |
| Endpoints API | 95% |
| Proyecto General | 95% |

### Estructura de Archivos de Prueba

```
packages/appointments/
└── tests/
    ├── __init__.py
    ├── test_models.py      # Pruebas de modelos
    ├── test_views.py       # Pruebas de vistas
    ├── test_services.py    # Pruebas de capa de servicios
    ├── test_forms.py       # Pruebas de formularios
    └── test_api.py         # Pruebas de endpoints API
```

---

## 2. Reglas de Arquitectura (ADR-001)

### Límites de Paquetes

**Ver:** [DECISIONES_ARQUITECTURA.md](DECISIONES_ARQUITECTURA.md) para contexto completo.

### Regla 1: Sin Importaciones Internas Entre Paquetes

```python
# ❌ MAL - Importación directa de otro paquete
from packages.crm_lite.models import Owner
from packages.vet_clinic.models import Pet

# ✅ BIEN - Usar get_model de Django para acoplamiento débil
from django.apps import apps
Owner = apps.get_model('crm_lite', 'Owner')
Pet = apps.get_model('vet_clinic', 'Pet')
```

### Regla 2: Usar Interfaces de Servicio

```python
# ❌ MAL - Manipulación directa de modelos desde otro paquete
from packages.appointments.models import Appointment
appointment = Appointment.objects.create(...)

# ✅ BIEN - Usar la interfaz de servicio
from packages.appointments.services import AppointmentService
appointment = AppointmentService.create_appointment(...)
```

### Regla 3: Ubicación del Código

| Tipo de Código | Ubicación | Ejemplo |
|----------------|-----------|---------|
| Reutilizable/Genérico | `packages/<nombre>/` | Lógica de reserva de citas |
| Específico de Pet-Friendly | `apps/website/` | Flujos personalizados del Dr. Pablo |
| Configuración del Proyecto | `config/` | Settings, URLs, WSGI |

```python
# packages/appointments/services.py - GENÉRICO
class AppointmentService:
    """Funciona para cualquier negocio que reserve citas."""
    pass

# apps/website/services.py - ESPECÍFICO
class PetFriendlyAppointmentService:
    """Lógica de citas específica de Pet-Friendly."""
    pass
```

### Regla 4: Dirección de Dependencias

```
apps/website/  →  puede importar de  →  packages/*
packages/*     →  puede importar de  →  Django, stdlib
packages/*     →  NO PUEDE importar  →  otros packages/*
```

### Regla 5: Paquetes Auto-contenidos

Cada paquete debe tener:
- Propio `models.py`
- Propio `services.py` (API pública)
- Propio directorio `tests/`
- Propias `templates/<nombre_paquete>/`
- Propios `static/<nombre_paquete>/`
- Propias `migrations/`

---

## 3. Estilo de Código

### Python

- Seguir PEP 8
- Usar type hints
- Docstrings para métodos públicos
- Longitud máxima de línea: 100 caracteres

```python
def create_appointment(
    owner_id: int,
    pet_id: int,
    service_type: str,
    scheduled_at: datetime
) -> Appointment:
    """
    Crear una nueva cita.

    Args:
        owner_id: ID del dueño de la mascota
        pet_id: ID de la mascota
        service_type: Tipo de servicio solicitado
        scheduled_at: Fecha y hora de la cita

    Returns:
        La instancia de Appointment creada

    Raises:
        ValidationError: Si el horario no está disponible
    """
    pass
```

### Django

- Usar vistas basadas en clases (preferir)
- Modelos pesados, vistas ligeras
- Lógica de negocio en servicios, no en vistas
- Usar el ORM de Django, evitar SQL crudo

### Plantillas

- Usar herencia de plantillas
- Componentes en `templates/components/`
- Parciales en `templates/partials/`
- Específicos de paquete en `templates/<nombre_paquete>/`

---

## 4. Estándares de Commits Git

### Formato de Mensaje de Commit

```
tipo(alcance): descripción breve

Explicación detallada si es necesaria.

Closes #X (para tareas)
Addresses #X (para bugs - SIN auto-cerrar)
```

### Tipos

| Tipo | Cuándo |
|------|--------|
| `feat` | Nueva característica |
| `fix` | Corrección de bug |
| `test` | Agregar/actualizar pruebas |
| `docs` | Documentación |
| `refactor` | Cambio de código que no corrige/agrega |
| `style` | Formateo, linting |
| `chore` | Tareas de mantenimiento |

### Ejemplos

```bash
# Característica
feat(appointments): agregar verificación de disponibilidad de horarios

# Corrección de bug (NO auto-cierra)
fix(store): corregir cálculo de total del carrito

Addresses #B-003

# Prueba
test(crm): agregar pruebas de servicio de perfil de dueño
```

---

## 5. Lista de Verificación Pre-Implementación

Copie esta lista antes de comenzar cualquier tarea:

```markdown
## Lista de Verificación Pre-Implementación

### Arquitectura
- [ ] Sé a qué paquete/app pertenece este código
- [ ] No estoy importando directamente de otros paquetes
- [ ] Estoy usando services.py para comunicación entre paquetes

### TDD
- [ ] Escribiré pruebas PRIMERO
- [ ] Tengo un archivo de prueba creado
- [ ] Entiendo cómo se ve "terminado"

### Estándares
- [ ] He revisado los criterios de aceptación
- [ ] Conozco la Definición de Terminado
- [ ] He verificado patrones existentes a seguir
```

---

## 6. Definición de Terminado (Global)

Una tarea está TERMINADA cuando:

- [ ] Todos los criterios de aceptación cumplidos
- [ ] Pruebas escritas y pasando (>95% cobertura)
- [ ] Sin violaciones de importación entre paquetes
- [ ] Código sigue guía de estilo
- [ ] Documentación actualizada
- [ ] Commit con mensaje apropiado
- [ ] PR revisado (si aplica)

---

## Referencias

- [DECISIONES_ARQUITECTURA.md](DECISIONES_ARQUITECTURA.md) - Detalles completos de ADR-001
- [../planning/TASK_INDEX.md](../planning/TASK_INDEX.md) - Todas las tareas con dependencias
- [../planning/MODULE_INTERFACES.md](../planning/MODULE_INTERFACES.md) - Contratos de API entre paquetes

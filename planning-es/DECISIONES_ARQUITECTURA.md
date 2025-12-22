# Registro de Decisiones de Arquitectura (ADR)

Este documento captura las decisiones arquitectónicas significativas tomadas durante el desarrollo de Pet-Friendly.

---

## ADR-001: Monorepo con Paquetes Extraíbles

**Fecha:** Diciembre 2025
**Estado:** Aceptado
**Responsables:** Nestor Wheelock

### Contexto

Pet-Friendly requiere 9 paquetes Django reutilizables que podrían beneficiar a otros proyectos:
- django-multilingual
- django-appointments
- django-simple-store
- django-ai-assistant
- django-crm-lite
- django-omnichannel
- django-competitive-intel
- django-vet-clinic
- django-accounting

Necesitábamos decidir si:
- **Opción A**: Construir cada paquete en su propio repositorio desde el inicio (9+ repos)
- **Opción B**: Construir todo junto y extraer paquetes después (1 repo)

### Decisión

**Construir todo junto primero (monorepo), extraer paquetes después.**

### Justificación

1. **Entregar más rápido** - El cliente necesita un sitio web funcional, no un ecosistema de paquetes
2. **Aprender límites** - El uso real revela las interfaces correctas de los paquetes
3. **CI/CD más simple** - Un repo, un conjunto de pruebas, un pipeline de despliegue
4. **Filosofía Django** - Las apps de Django están diseñadas para ser extraíbles
5. **Pragmático** - Evitar sobre-ingeniería antes de conocer las necesidades reales
6. **Iteración** - Más fácil refactorizar límites cuando todo está en un solo lugar

### Estructura del Proyecto

```
petfriendly/
├── config/                    # Configuración del proyecto Django
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
├── packages/                  # Futuros paquetes instalables via pip
│   ├── multilingual/          # → django-multilingual
│   ├── appointments/          # → django-appointments
│   ├── simple_store/          # → django-simple-store
│   ├── ai_assistant/          # → django-ai-assistant
│   ├── crm_lite/              # → django-crm-lite
│   ├── omnichannel/           # → django-omnichannel
│   ├── competitive_intel/     # → django-competitive-intel
│   ├── vet_clinic/            # → django-vet-clinic
│   └── accounting/            # → django-accounting
│
├── apps/
│   └── website/               # Código específico de Pet-Friendly SOLAMENTE
│
├── templates/
├── static/
├── locale/
├── media/
└── manage.py
```

### Reglas (Disciplina Requerida)

#### 1. Sin Importaciones Internas Entre Paquetes

```python
# MAL - Importación directa de otro paquete
from packages.crm_lite.models import Owner
from packages.vet_clinic.models import Pet

# BIEN - Usar get_model de Django para acoplamiento débil
from django.apps import apps
Owner = apps.get_model('crm_lite', 'Owner')
Pet = apps.get_model('vet_clinic', 'Pet')
```

#### 2. Interfaces Explícitas Entre Paquetes

Cada paquete define un `services.py` con su API pública:

```python
# packages/appointments/services.py
class AppointmentService:
    @staticmethod
    def get_available_slots(date, service_type):
        """API pública para verificar disponibilidad."""
        pass

    @staticmethod
    def book_appointment(owner_id, pet_id, slot, service):
        """API pública para reservar."""
        pass
```

Otros paquetes importan de services, nunca directamente de models:

```python
# BIEN
from packages.appointments.services import AppointmentService

# MAL
from packages.appointments.models import Appointment
```

#### 3. Código Específico de Pet-Friendly en apps/website/

La lógica de negocio específica de la clínica veterinaria va en `apps/website/`:

```python
# apps/website/services.py
class PetFriendlyService:
    """Lógica de negocio específica de Pet-Friendly."""

    def process_travel_certificate(self, pet, destination):
        # Usa el paquete vet_clinic pero agrega lógica específica de PF
        pass
```

Los paquetes permanecen genéricos y reutilizables para otros negocios.

#### 4. Cada Paquete es Auto-contenido

Cada paquete en `packages/` contiene:
```
packages/appointments/
├── __init__.py
├── admin.py           # Configuración de admin propia
├── apps.py            # Configuración de app Django
├── models.py          # Modelos propios
├── views.py           # Vistas propias
├── urls.py            # Patrones URL propios
├── services.py        # API pública
├── forms.py           # Formularios propios
├── templates/         # Plantillas propias
│   └── appointments/
├── static/            # Archivos estáticos propios
│   └── appointments/
├── tests/             # Suite de pruebas propia
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
└── migrations/        # Migraciones propias
```

#### 5. Dirección de Dependencias

```
┌─────────────────────────────────────────┐
│           apps/website/                  │
│      (Específico de Pet-Friendly)       │
│                                          │
│   Puede importar de CUALQUIER paquete    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│            packages/                     │
│                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  citas  │ │ tienda  │ │   ia    │   │
│  │         │ │         │ │asistente│   │
│  └─────────┘ └─────────┘ └─────────┘   │
│                                          │
│  Los paquetes NO deben importar entre sí │
│  Usar interfaces/señales en su lugar     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│     Django + Biblioteca Estándar Python  │
└─────────────────────────────────────────┘
```

### Criterios de Extracción

Un paquete está listo para extraerse a su propio repositorio cuando:

- [ ] Tiene cobertura de pruebas completa (>95%)
- [ ] No tiene importaciones de otros directorios `packages/`
- [ ] Tiene API pública documentada (services.py)
- [ ] Ha sido usado en producción por 1+ mes
- [ ] Tiene README con instrucciones de instalación y uso
- [ ] Tiene pyproject.toml o setup.py listo
- [ ] Todas las migraciones son estables (no se esperan más cambios de esquema)

### Proceso de Extracción

Cuando esté listo para extraer un paquete:

1. Crear nuevo repositorio (ej., `django-appointments`)
2. Copiar directorio del paquete al nuevo repo
3. Agregar archivos de empaquetado (pyproject.toml, README, LICENSE)
4. Publicar en PyPI (o índice privado)
5. En petfriendly, reemplazar `packages/appointments/` con pip install
6. Actualizar importaciones si es necesario
7. Archivar el paquete del monorepo

### Consecuencias

**Positivas:**
- Velocidad de desarrollo inicial más rápida
- Interfaces validadas en el mundo real antes de extracción
- Flujo de trabajo de desarrollo más simple (un repo)
- Refactorización más fácil durante desarrollo temprano

**Negativas:**
- Requiere disciplina para mantener límites
- Debe hacer cumplir activamente reglas de importación en revisión de código
- Riesgo de acoplamiento si se ignoran las reglas

**Riesgos y Mitigaciones:**
- "Extraer después" se vuelve deuda técnica → Revisar preparación para extracción después de cada Época
- Los límites se vuelven borrosos → Linting automatizado para importaciones entre paquetes
- Se desarrolla acoplamiento fuerte → Revisiones de arquitectura regulares

### Calendario de Revisión

Revisar preparación para extracción de paquetes en:
- Fin de Época 2 (después de que citas + mascotas funcionen)
- Fin de Época 4 (después del centro de comunicaciones)
- Fin de Época 6 (revisión final antes de cualquier extracción)

---

## ADRs Futuros

A medida que se tomen nuevas decisiones arquitectónicas, se agregarán aquí:

- ADR-002: (Reservado)
- ADR-003: (Reservado)

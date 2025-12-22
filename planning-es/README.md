# Veterinaria Pet-Friendly - Documentación de Planificación

**Cliente:** Dr. Pablo Rojo Mendoza - Veterinaria Pet-Friendly, Puerto Morelos, México
**Preparado por:** Nestor Wheelock - South City Computer
**Fecha:** Diciembre 2025
**Estado:** Fase SPEC - Planificación e Investigación

---

## Resumen del Proyecto

Plataforma integral de sitio web y gestión veterinaria con enfoque en IA para Veterinaria Pet-Friendly en Puerto Morelos, Quintana Roo, México.

### Visión
Crear un sistema moderno con IA como interfaz principal que revolucione la forma en que las clínicas veterinarias interactúan con los dueños de mascotas, gestionan citas, procesan pagos y se comunican con los clientes.

### Características Principales
- **Interfaz con IA** - Chat como método principal de interacción
- **Gestión de Mascotas** - Perfiles completos y registros médicos
- **Sistema de Citas** - Reservas en línea con recordatorios
- **Tienda en Línea** - E-commerce con carrito y Stripe
- **Comunicaciones Omnicanal** - Email, SMS, WhatsApp unificados
- **CRM de Clientes** - Perfiles, segmentación, lealtad
- **Contabilidad** - Facturación CFDI, reportes financieros
- **Multilingüe** - Español, inglés, y más idiomas con IA

---

## Estructura de Documentos

```
planning-es/
├── README.md                    # Este archivo
├── PROJECT_CHARTER.md           # Carta del proyecto
├── SPEC_SUMMARY.md              # Resumen de especificaciones
├── stories/                     # Historias de usuario
│   ├── S-001-*.md              # Historia por historia
│   └── ...
├── tasks/                       # Desglose de tareas
│   ├── T-001-*.md              # Tarea por tarea
│   └── ...
└── wireframes/                  # Diseños de interfaz
    ├── 01-homepage.txt          # Página principal
    └── ...
```

---

## Épocas de Desarrollo

### Época 1: Fundación + Núcleo de IA
**Historias:** S-001, S-002, S-011, S-023
**Duración Estimada:** 2 semanas

- Arquitectura modular Django
- Autenticación (Google OAuth + email/teléfono)
- Sistema bilingüe (ES/EN)
- Capa de servicios de IA (OpenRouter, llamadas de herramientas)
- Modelos de base de conocimiento
- Interfaz de chat (cliente + admin)
- Páginas de información básica

### Época 2: Citas + Mascotas
**Historias:** S-003, S-004, S-012, S-013, S-021, S-022
**Duración Estimada:** 2 semanas

- Perfiles de mascotas (básico → médico)
- Reserva de citas vía IA
- Carga de documentos/fotos
- Procesamiento OCR/visión
- Recordatorios por email
- Certificados de viaje

### Época 3: Comercio Electrónico
**Historias:** S-005, S-010, S-020, S-024
**Duración Estimada:** 2 semanas

- Catálogo de productos
- Carrito de compras
- Checkout con Stripe
- Gestión de pedidos
- Facturación y CFDI
- Gestión de inventario

### Época 4: Centro de Comunicaciones
**Historias:** S-006, S-015, S-025
**Duración Estimada:** 2 semanas

- API de WhatsApp Business
- Integración SMS
- Voz (escalamiento)
- Lógica de escalamiento de recordatorios
- Bandeja unificada
- Servicios de emergencia

### Época 5: CRM + Marketing
**Historias:** S-007, S-009, S-014, S-016, S-018, S-019
**Duración Estimada:** 2 semanas

- Perfiles de clientes
- Análisis de historial de compras
- Sistema de lealtad y puntos
- Reseñas y testimonios
- SEO y blog
- Email marketing

### Época 6: Gestión de Práctica
**Historias:** S-008, S-017, S-026
**Duración Estimada:** 2 semanas

- Programación de personal
- Notas clínicas internas
- Reportes y analíticas
- Sistema contable completo
- Exportes de cumplimiento

---

## Pila Tecnológica

| Componente | Tecnología |
|------------|------------|
| **Backend** | Django 5.x |
| **Frontend** | HTMX + Alpine.js |
| **Base de Datos** | PostgreSQL |
| **Caché** | Redis |
| **Tareas** | Celery |
| **IA** | OpenRouter (Claude) |
| **Pagos** | Stripe México |
| **Email** | Amazon SES |
| **SMS** | Twilio |
| **WhatsApp** | Meta Cloud API |
| **Hosting** | AWS México |
| **CFDI** | Facturama |

---

## Módulos Reutilizables

El proyecto se construye como 9 paquetes instalables vía pip:

1. **django-multilingual** - Traducción con IA
2. **django-appointments** - Reservas de servicios
3. **django-simple-store** - Comercio electrónico
4. **django-ai-assistant** - Chat e IA
5. **django-crm-lite** - Gestión de contactos
6. **django-omnichannel** - Comunicaciones multicanal
7. **django-competitive-intel** - Seguimiento de competencia
8. **django-vet-clinic** - Perfiles de mascotas y registros médicos
9. **django-accounting** - Contabilidad de doble entrada

---

## Próximos Pasos

1. Revisión del cliente de documentos SPEC
2. Aprobación del cliente para comenzar BUILD
3. Configuración inicial del proyecto Django
4. Desarrollo por épocas

---

## Contacto

**Cliente:** Dr. Pablo Rojo Mendoza
- Email: pablorojomendoza@gmail.com
- WhatsApp: +52 998 316 2438

**Desarrollador:** Nestor Wheelock
- South City Computer

---

*Documento actualizado: Diciembre 2025*

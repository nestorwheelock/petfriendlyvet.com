# Carta del Proyecto: Veterinaria Pet-Friendly

**Preparado por:** Nestor Wheelock - South City Computer
**Cliente:** Dr. Pablo Rojo Mendoza
**Fecha:** Diciembre 2025
**Versión:** 2.0

---

## Resumen Ejecutivo

Desarrollo de una plataforma web integral con enfoque en IA para Veterinaria Pet-Friendly ubicada en Puerto Morelos, Quintana Roo, México. El sistema combinará gestión de clínica veterinaria, comercio electrónico, CRM, y comunicaciones multicanal, todo accesible a través de una interfaz de chat inteligente.

---

## Visión del Proyecto

### Lo Que Estamos Construyendo

Una plataforma veterinaria moderna donde la **IA es la interfaz principal**, no un añadido. Los clientes y el personal interactúan naturalmente a través de chat para:

**Para Clientes:**
- Aprender sobre la clínica, servicios, horarios, ubicación
- Reservar y gestionar citas
- Ordenar y reordenar productos
- Acceder a información y registros de sus mascotas
- Subir documentos y fotos
- Comunicarse con Dr. Pablo (reemplaza el caos de WhatsApp)

**Para Personal/Admin:**
- Todas las operaciones CRUD vía lenguaje natural
- Crear y gestionar contenido
- Buscar en todos los datos
- Gestionar citas y horarios
- Procesar documentos con OCR/visión
- Gestionar inventario y pedidos
- Ver reportes y analíticas

### Por Qué Lo Estamos Construyendo

1. **Pet-Friendly no tiene sitio web** - Solo listados de directorio y redes sociales
2. **Ningún competidor local tiene sitio web real** - Oportunidad de ser primero
3. **El caos de WhatsApp** - Comunicaciones no organizadas con clientes
4. **Sistema actual limitado** - OkVet.co es básico y centrado en Colombia
5. **Comunidad bilingüe** - Puerto Morelos tiene expats que necesitan servicio en inglés

---

## Alcance del Proyecto

### Dentro del Alcance

| Área | Características |
|------|-----------------|
| **Sitio Web Público** | Página principal, servicios, tienda, contacto, blog |
| **Portal de Clientes** | Dashboard, mascotas, citas, pedidos, documentos |
| **Panel de Admin** | Gestión completa, reportes, configuración |
| **Interfaz de IA** | Chat para clientes y personal |
| **Comercio** | Catálogo, carrito, checkout, Stripe |
| **Comunicaciones** | Email, SMS, WhatsApp, bandeja unificada |
| **CRM** | Perfiles de clientes, segmentación, lealtad |
| **Contabilidad** | Facturación, CFDI, cuentas por pagar/cobrar |

### Fuera del Alcance (Versión 1.0)

- Integración directa con OkVet.co (investigación pendiente)
- Aplicación móvil nativa (el sitio web es responsive)
- Integraciones con laboratorios externos
- Sistema de nómina completo
- Múltiples sucursales (una sola clínica)

---

## Arquitectura Técnica

### Principios de Diseño

1. **IA-Primero** - Chat es la interfaz principal
2. **Modular** - 9 paquetes reutilizables
3. **Multilingüe Nativo** - Traducción automática con IA
4. **Móvil-Primero** - Diseño responsive
5. **Seguro** - Autenticación robusta, auditoría

### Pila Tecnológica

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                                │
│   HTMX + Alpine.js + TailwindCSS + Chart.js                 │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND                                 │
│   Django 5.x + Django REST Framework + Celery               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE IA                               │
│   OpenRouter API (Claude) + Llamadas de Herramientas        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    SERVICIOS EXTERNOS                        │
│   Stripe │ Twilio │ WhatsApp │ Amazon SES │ Facturama       │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    DATOS                                     │
│   PostgreSQL + Redis + S3 (archivos)                        │
└─────────────────────────────────────────────────────────────┘
```

### 9 Módulos Reutilizables

| Módulo | Descripción | Industrias |
|--------|-------------|------------|
| **django-multilingual** | Traducción con IA | Cualquier sitio multilingüe |
| **django-appointments** | Reserva de servicios | Salones, dentistas, consultores |
| **django-simple-store** | Comercio electrónico | Cualquier negocio pequeño |
| **django-ai-assistant** | Interfaz de chat | Cualquier sitio con IA |
| **django-crm-lite** | Perfiles de contactos | Cualquier negocio |
| **django-omnichannel** | Comunicaciones | Cualquier comunicación con clientes |
| **django-competitive-intel** | Seguimiento de competencia | Cualquier negocio competitivo |
| **django-vet-clinic** | Perfiles de mascotas | Clínicas veterinarias |
| **django-accounting** | Contabilidad | Cualquier negocio |

---

## Integraciones Clave

### Stripe México
- Pagos con tarjeta en línea
- OXXO para pagos en efectivo
- Suscripciones para planes de bienestar
- **Comisión:** 3.6% + $3.00 MXN

### WhatsApp Business API
- Mensajes de plantilla para recordatorios
- Conversaciones bidireccionales
- Requiere aprobación de Meta (2-4 semanas)

### Facturama (CFDI)
- Facturas electrónicas SAT
- CFDI 4.0 compliant
- Notas de crédito
- Complementos de pago

### Amazon SES
- Email transaccional
- Campañas de marketing
- **Costo:** $0.10 por 1,000 emails

### Twilio
- SMS para recordatorios
- Números mexicanos locales
- **Costo:** ~$0.008 por mensaje

---

## Épocas de Desarrollo

### Época 1: Fundación + Núcleo de IA
**Duración:** 2 semanas
**Entregable:** Sitio donde usuarios pueden chatear y obtener información

- Arquitectura modular Django
- Autenticación (Google OAuth + email/teléfono)
- Sistema multilingüe
- Servicio de IA (OpenRouter)
- Base de conocimiento
- Interfaz de chat
- Páginas informativas

### Época 2: Citas + Mascotas
**Duración:** 2 semanas
**Entregable:** Sistema funcional de citas con registros de mascotas

- Perfiles de mascotas
- Registros médicos
- Reserva de citas vía IA
- Carga de documentos
- Recordatorios por email
- Certificados de viaje

### Época 3: Comercio Electrónico
**Duración:** 2 semanas
**Entregable:** Tienda en línea funcionando

- Catálogo de productos
- Carrito de compras
- Checkout con Stripe
- Gestión de pedidos
- Facturación CFDI
- Gestión de inventario

### Época 4: Centro de Comunicaciones
**Duración:** 2 semanas
**Entregable:** Todas las comunicaciones en un lugar

- Integración WhatsApp
- Integración SMS
- Bandeja unificada
- Escalamiento automático
- Servicios de emergencia
- Red de referidos

### Época 5: CRM + Marketing
**Duración:** 2 semanas
**Entregable:** Capacidades completas de CRM

- Perfiles de clientes
- Segmentación
- Programa de lealtad
- Reseñas
- Blog y SEO
- Email marketing

### Época 6: Gestión de Práctica
**Duración:** 2 semanas
**Entregable:** Sistema de gestión completo

- Gestión de personal
- Notas clínicas
- Reportes y analíticas
- Contabilidad completa
- Exportes de auditoría

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Aprobación WhatsApp demora | Media | Alto | Aplicar temprano (4+ semanas antes) |
| Cambios de alcance | Alta | Medio | Alcance bloqueado después de aprobación |
| Integración Stripe fallida | Baja | Alto | Alternativas: Conekta, MercadoPago |
| Datos de OkVet.co | Media | Medio | Investigar exportación, entrada manual como respaldo |
| Contenido del cliente tarde | Alta | Medio | Checklist enviado, seguimiento regular |

---

## Criterios de Éxito

### Técnicos
- [ ] >95% cobertura de pruebas
- [ ] Tiempo de respuesta <200ms (percentil 95)
- [ ] Carga de página <2 segundos
- [ ] 99.9% uptime
- [ ] Cero vulnerabilidades de seguridad críticas

### Negocio
- [ ] Sitio web en vivo y funcionando
- [ ] Al menos 10 citas reservadas en línea primer mes
- [ ] Al menos 5 pedidos en línea primer mes
- [ ] Reducción del 50% en mensajes WhatsApp manuales
- [ ] Satisfacción del cliente >4.5/5

---

## Proceso de Aprobación

### Puerta 1: Aprobación SPEC
- [ ] Cliente revisa todos los documentos de planificación
- [ ] Cliente aprueba alcance y entregables
- [ ] Alcance bloqueado - cambios requieren nueva aprobación

### Puerta 2: Aprobación de Aceptación
- [ ] Cliente prueba todas las funcionalidades
- [ ] Cliente verifica que cumple con criterios de aceptación
- [ ] Cliente aprueba para producción

---

## Información de Contacto

**Cliente:**
- Dr. Pablo Rojo Mendoza
- Veterinaria Pet-Friendly
- Puerto Morelos, Quintana Roo, México
- pablorojomendoza@gmail.com
- +52 998 316 2438

**Desarrollador:**
- Nestor Wheelock
- South City Computer

---

*Última actualización: Diciembre 2025*

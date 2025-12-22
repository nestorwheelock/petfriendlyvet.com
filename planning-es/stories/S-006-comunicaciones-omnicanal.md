# S-006: Comunicaciones Omnicanal

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Alta
**Estimación:** 5 días
**Época:** 4
**Estado:** Pendiente

## Historia de Usuario
**Como** administrador de la clínica
**Quiero** gestionar todas las comunicaciones desde un solo lugar
**Para que** ningún mensaje de cliente se pierda y pueda responder eficientemente

## Criterios de Aceptación
- [ ] Bandeja unificada muestra mensajes de todos los canales
- [ ] Puedo ver y responder mensajes de WhatsApp
- [ ] Puedo ver y responder emails
- [ ] Puedo ver y responder SMS
- [ ] Puedo asignar conversaciones a personal
- [ ] Puedo marcar conversaciones como resueltas
- [ ] Recordatorios automáticos funcionan
- [ ] Escalamiento automático si no hay respuesta

## Definición de Hecho
- [ ] Integración WhatsApp funcionando
- [ ] Integración email funcionando
- [ ] Integración SMS funcionando
- [ ] Bandeja unificada responsiva
- [ ] Pruebas >95% cobertura

## Tareas Relacionadas
- T-044: Modelos de Comunicación
- T-045: Integración Email (Amazon SES)
- T-046: Integración SMS (Twilio)
- T-047: Integración WhatsApp
- T-048: Bandeja Unificada
- T-049: Motor de Escalamiento

## Wireframe
Ver: `planning/wireframes/16-communications-inbox.txt`

## Canales de Comunicación

### Email (Amazon SES)
- **Costo:** $0.10 por 1,000 emails
- **Usos:** Confirmaciones, facturas, newsletters
- **Configuración:** Verificar dominio, SPF, DKIM

### SMS (Twilio)
- **Costo:** ~$0.008 por mensaje
- **Usos:** Recordatorios de citas, confirmaciones urgentes
- **Configuración:** Número local mexicano

### WhatsApp (Meta Cloud API)
- **Costo:** ~$0.05 por mensaje de plantilla
- **Usos:** Recordatorios, confirmaciones, comunicación bidireccional
- **Configuración:** Verificación de negocio (2-4 semanas)

## Plantillas de Mensajes

### Recordatorio de Cita (WhatsApp)
```
Hola {{nombre_cliente}},

Le recordamos que tiene una cita programada:

📅 Fecha: {{fecha_cita}}
🕐 Hora: {{hora_cita}}
🐾 Paciente: {{nombre_mascota}}
🏥 Servicio: {{tipo_servicio}}

Por favor confirme su asistencia respondiendo:
✅ SÍ para confirmar
❌ NO para cancelar

Veterinaria Pet-Friendly
📍 Puerto Morelos, Q.R.
📞 998 316 2438
```

### Confirmación de Pedido (Email)
```
Asunto: ¡Pedido confirmado! #{{numero_pedido}}

Hola {{nombre_cliente}},

Gracias por tu compra en Veterinaria Pet-Friendly.

📦 Resumen de tu pedido:
{{lista_productos}}

💰 Total: ${{total}} MXN

📍 Método de entrega: {{metodo_entrega}}

Te notificaremos cuando tu pedido esté listo.

¡Gracias por confiar en nosotros!
```

## Lógica de Escalamiento

```
Recordatorio de cita:
┌─────────────────────────────────────────────────────┐
│ 48 horas antes                                       │
│ └─> Enviar recordatorio por WhatsApp                │
│                                                      │
│ 24 horas antes (si no confirmó)                     │
│ └─> Enviar recordatorio por SMS                     │
│                                                      │
│ 12 horas antes (si no confirmó)                     │
│ └─> Enviar email                                    │
│                                                      │
│ 6 horas antes (si no confirmó)                      │
│ └─> Llamar automáticamente (mensaje de voz)         │
│     └─> Notificar al personal para llamada manual   │
└─────────────────────────────────────────────────────┘
```

## Bandeja Unificada

### Características
- Vista de todas las conversaciones
- Filtros por canal, estado, asignado
- Búsqueda por cliente o contenido
- Indicadores de no leído
- Tiempo de respuesta visible
- Asignación a personal

### Estados de Conversación
| Estado | Descripción |
|--------|-------------|
| Nueva | Mensaje sin leer |
| Abierta | En proceso de atención |
| En espera | Esperando respuesta del cliente |
| Escalada | Requiere atención urgente |
| Resuelta | Conversación cerrada |

## Métricas a Rastrear
- Tiempo promedio de respuesta
- Conversaciones por canal
- Tasa de resolución
- Satisfacción del cliente
- Mensajes no contestados

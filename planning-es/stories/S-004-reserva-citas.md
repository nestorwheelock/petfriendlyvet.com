# S-004: Reserva de Citas vía IA

> **LECTURA OBLIGATORIA:** Antes de implementar, revise [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Alta
**Estimación:** 4 días
**Época:** 2
**Estado:** Pendiente

## Historia de Usuario
**Como** dueño de mascota
**Quiero** reservar citas a través del chat con IA
**Para que** pueda programar visitas de forma rápida y natural

## Criterios de Aceptación
- [ ] Puedo pedir una cita a través del chat
- [ ] El chat me muestra horarios disponibles
- [ ] Puedo seleccionar fecha y hora
- [ ] Puedo especificar el servicio que necesito
- [ ] Puedo elegir cuál mascota llevará
- [ ] Recibo confirmación de la cita
- [ ] Puedo ver mis citas próximas en mi dashboard
- [ ] Puedo cancelar o reprogramar citas

## Definición de Hecho
- [ ] Sistema de reservas completo
- [ ] Integración con calendario
- [ ] Notificaciones configuradas
- [ ] Pruebas >95% cobertura

## Tareas Relacionadas
- T-020: Modelos de Citas
- T-021: Modelos de Tipos de Servicio
- T-022: Sistema de Disponibilidad
- T-023: Herramientas de IA para Citas

## Wireframe
Ver: `planning/wireframes/05-appointment.txt`

## Ejemplo de Conversación

```
Usuario: Quiero hacer una cita para mi perro

IA: ¡Con gusto te ayudo a programar una cita! 🐕

Veo que tienes registrado a "Max" (Golden Retriever).
¿Es para Max la cita?

Usuario: Sí, para Max

IA: Perfecto. ¿Qué tipo de servicio necesitas?

1. 🩺 Consulta general
2. 💉 Vacunación
3. ✂️ Estética/Baño
4. 🦷 Limpieza dental
5. 🔬 Estudios de laboratorio

Usuario: Consulta general

IA: Entendido, consulta general para Max.

📅 Fechas disponibles esta semana:
- Martes 24: 10:00, 11:00, 16:00
- Miércoles 25: 9:00, 14:00, 17:00
- Jueves 26: 10:00, 15:00

¿Cuál horario te conviene mejor?

Usuario: El martes a las 10

IA: ¡Perfecto! Tu cita está confirmada:

📋 **Confirmación de Cita**
━━━━━━━━━━━━━━━━━━━━━━
🐕 Paciente: Max
📅 Fecha: Martes 24 de Diciembre
🕐 Hora: 10:00 AM
🏥 Servicio: Consulta General
📍 Veterinaria Pet-Friendly, Puerto Morelos

Te enviaremos un recordatorio un día antes.
¿Hay algo más en lo que pueda ayudarte?
```

## Servicios Disponibles

| Servicio | Duración | Precio Base |
|----------|----------|-------------|
| Consulta General | 30 min | $450 MXN |
| Vacunación | 15 min | $350 MXN |
| Baño Pequeño | 60 min | $250 MXN |
| Baño Grande | 90 min | $400 MXN |
| Limpieza Dental | 60 min | $1,200 MXN |
| Estudios Lab | 30 min | Variable |
| Cirugía | Variable | Variable |

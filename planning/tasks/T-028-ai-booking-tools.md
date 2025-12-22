# T-028: AI Booking Tools

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement AI tools for conversational appointment booking
**Related Story**: S-004
**Epoch**: 2
**Estimate**: 6 hours

### Constraints
**Allowed File Paths**: apps/appointments/tools/, apps/ai_assistant/
**Forbidden Paths**: None

### Deliverables
- [ ] check_availability tool
- [ ] book_appointment tool
- [ ] cancel_appointment tool
- [ ] reschedule_appointment tool
- [ ] list_my_appointments tool
- [ ] get_appointment_details tool

### Implementation Details

#### Tool: check_availability
```python
@tool(
    name="check_availability",
    description="Check available appointment slots for a service on a specific date",
    permission="public",
    module="appointments"
)
def check_availability(
    service_name: str,
    date: str,  # YYYY-MM-DD format
    pet_id: int = None
) -> dict:
    """Check available slots for booking."""

    try:
        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d").date()

        # Find service
        service = ServiceType.objects.filter(
            Q(name__icontains=service_name) |
            Q(name_es__icontains=service_name) |
            Q(name_en__icontains=service_name),
            is_bookable_online=True
        ).first()

        if not service:
            return {
                "success": False,
                "error": f"Servicio '{service_name}' no encontrado"
            }

        # Get slots
        slots = AvailabilityService().get_available_slots(target_date, service)

        return {
            "success": True,
            "date": date,
            "service": service.name,
            "duration_minutes": service.duration_minutes,
            "price": str(service.price) if service.price else service.price_text,
            "available_slots": [s.strftime("%H:%M") for s in slots],
            "slots_count": len(slots)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
```

#### Tool: book_appointment
```python
@tool(
    name="book_appointment",
    description="Book an appointment for a pet",
    permission="customer",  # Must be logged in
    module="appointments"
)
def book_appointment(
    pet_id: int,
    service_name: str,
    date: str,
    time: str,
    reason: str = ""
) -> dict:
    """Create a new appointment."""

    try:
        # Get pet (verifies ownership via context.user)
        pet = Pet.objects.get(id=pet_id, owner=context.user)

        # Find service
        service = ServiceType.objects.get(
            Q(name__icontains=service_name) |
            Q(name_es__icontains=service_name)
        )

        # Parse date/time
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        target_time = datetime.strptime(time, "%H:%M").time()

        # Verify slot still available
        slots = AvailabilityService().get_available_slots(target_date, service)
        if target_time not in slots:
            return {
                "success": False,
                "error": "Este horario ya no está disponible"
            }

        # Create appointment
        appointment = Appointment.objects.create(
            pet=pet,
            service=service,
            scheduled_date=target_date,
            scheduled_time=target_time,
            duration_minutes=service.duration_minutes,
            reason=reason,
            status='requested',
            booked_via='ai_chat',
            created_by=context.user
        )

        # Send confirmation request (async)
        send_appointment_confirmation.delay(appointment.id)

        return {
            "success": True,
            "appointment_id": appointment.id,
            "pet_name": pet.name,
            "service": service.name,
            "date": date,
            "time": time,
            "status": "requested",
            "message": f"Cita solicitada para {pet.name}. Te enviaremos confirmación pronto."
        }

    except Pet.DoesNotExist:
        return {"success": False, "error": "Mascota no encontrada"}
    except ServiceType.DoesNotExist:
        return {"success": False, "error": "Servicio no encontrado"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

#### Tool: list_my_appointments
```python
@tool(
    name="list_my_appointments",
    description="List upcoming appointments for the user's pets",
    permission="customer",
    module="appointments"
)
def list_my_appointments(
    include_past: bool = False,
    pet_id: int = None
) -> dict:
    """List user's appointments."""

    appointments = Appointment.objects.filter(
        pet__owner=context.user
    ).select_related('pet', 'service')

    if pet_id:
        appointments = appointments.filter(pet_id=pet_id)

    if not include_past:
        appointments = appointments.filter(
            scheduled_date__gte=timezone.now().date()
        )

    appointments = appointments.order_by('scheduled_date', 'scheduled_time')[:10]

    return {
        "success": True,
        "count": appointments.count(),
        "appointments": [
            {
                "id": a.id,
                "pet_name": a.pet.name,
                "service": a.service.name,
                "date": a.scheduled_date.strftime("%Y-%m-%d"),
                "time": a.scheduled_time.strftime("%H:%M"),
                "status": a.status,
                "status_display": a.get_status_display()
            }
            for a in appointments
        ]
    }
```

#### Tool: cancel_appointment
```python
@tool(
    name="cancel_appointment",
    description="Cancel an existing appointment",
    permission="customer",
    module="appointments"
)
def cancel_appointment(
    appointment_id: int,
    reason: str = ""
) -> dict:
    """Cancel an appointment."""

    try:
        appointment = Appointment.objects.get(
            id=appointment_id,
            pet__owner=context.user
        )

        # Check if can be cancelled
        if appointment.status in ['completed', 'cancelled', 'no_show']:
            return {
                "success": False,
                "error": "Esta cita no puede ser cancelada"
            }

        # Check cancellation policy (24 hours)
        if appointment.datetime < timezone.now() + timedelta(hours=24):
            return {
                "success": False,
                "error": "Las citas deben cancelarse con al menos 24 horas de anticipación"
            }

        # Cancel
        appointment.status = 'cancelled'
        appointment.cancelled_at = timezone.now()
        appointment.cancellation_reason = reason
        appointment.save()

        # Send notification
        send_cancellation_notification.delay(appointment.id)

        return {
            "success": True,
            "message": f"Cita para {appointment.pet.name} el {appointment.scheduled_date} cancelada"
        }

    except Appointment.DoesNotExist:
        return {"success": False, "error": "Cita no encontrada"}
```

#### Tool: reschedule_appointment
```python
@tool(
    name="reschedule_appointment",
    description="Reschedule an existing appointment to a new date/time",
    permission="customer",
    module="appointments"
)
def reschedule_appointment(
    appointment_id: int,
    new_date: str,
    new_time: str
) -> dict:
    """Reschedule an appointment."""

    try:
        appointment = Appointment.objects.get(
            id=appointment_id,
            pet__owner=context.user
        )

        # Check if can be rescheduled
        if appointment.status not in ['requested', 'confirmed']:
            return {
                "success": False,
                "error": "Esta cita no puede ser reprogramada"
            }

        # Parse new date/time
        target_date = datetime.strptime(new_date, "%Y-%m-%d").date()
        target_time = datetime.strptime(new_time, "%H:%M").time()

        # Verify availability
        slots = AvailabilityService().get_available_slots(
            target_date,
            appointment.service
        )
        if target_time not in slots:
            return {
                "success": False,
                "error": "Este horario no está disponible"
            }

        # Store old info
        old_date = appointment.scheduled_date
        old_time = appointment.scheduled_time

        # Update
        appointment.scheduled_date = target_date
        appointment.scheduled_time = target_time
        appointment.status = 'requested'  # Needs reconfirmation
        appointment.save()

        # Send notification
        send_reschedule_notification.delay(
            appointment.id,
            old_date,
            old_time
        )

        return {
            "success": True,
            "message": f"Cita reprogramada de {old_date} a {new_date} {new_time}"
        }

    except Appointment.DoesNotExist:
        return {"success": False, "error": "Cita no encontrada"}
```

### Conversation Flow Examples

**Booking Flow:**
```
User: Necesito llevar a Luna a vacunar

AI: ¡Claro! Veo que tienes a Luna registrada. ¿Qué día te gustaría?
    [Uses: get_pet_info for Luna]

User: El próximo lunes

AI: Perfecto. Para el lunes 23 de diciembre, tengo estos horarios disponibles para vacunación:
    • 9:00 AM
    • 10:30 AM
    • 2:00 PM
    • 4:30 PM
    ¿Cuál prefieres?
    [Uses: check_availability]

User: Las 10:30 está bien

AI: ✅ Listo! He reservado la cita:
    🐕 Luna
    💉 Vacunación
    📅 Lunes 23 de diciembre, 10:30 AM
    💰 $380 MXN

    Te enviaré un recordatorio por WhatsApp.
    [Uses: book_appointment]
```

### Test Cases
- [ ] check_availability returns slots
- [ ] book_appointment creates record
- [ ] list_my_appointments filters correctly
- [ ] cancel_appointment enforces policy
- [ ] reschedule_appointment validates availability
- [ ] Permission checks work
- [ ] Error handling graceful

### Definition of Done
- [ ] All 6 tools implemented
- [ ] Tools registered in registry
- [ ] Conversation flows work
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-010: Tool Calling Framework
- T-027: Appointment Models

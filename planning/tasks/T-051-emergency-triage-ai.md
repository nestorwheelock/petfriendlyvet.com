# T-051: AI Emergency Triage Tools

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement AI tools for emergency triage and routing
**Related Story**: S-015
**Epoch**: 4
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/vet_clinic/, apps/ai_assistant/tools/
**Forbidden Paths**: None

### Deliverables
- [ ] report_emergency tool
- [ ] triage_symptoms tool
- [ ] get_first_aid tool
- [ ] find_emergency_vet tool
- [ ] Emergency notification system

### Implementation Details

#### AI Tool Schemas
```python
EMERGENCY_TOOLS = [
    {
        "name": "report_emergency",
        "description": "Report a pet emergency and get immediate guidance",
        "permission": "public",
        "module": "emergency",
        "parameters": {
            "type": "object",
            "properties": {
                "pet_name": {
                    "type": "string",
                    "description": "Name of the pet"
                },
                "species": {
                    "type": "string",
                    "enum": ["dog", "cat", "bird", "rabbit", "reptile", "other"],
                    "description": "Type of animal"
                },
                "symptoms": {
                    "type": "string",
                    "description": "Description of symptoms or emergency"
                },
                "duration": {
                    "type": "string",
                    "description": "How long symptoms have been present"
                },
                "is_conscious": {
                    "type": "boolean",
                    "description": "Is the pet conscious and responsive?"
                },
                "is_breathing": {
                    "type": "boolean",
                    "description": "Is the pet breathing?"
                },
                "is_bleeding": {
                    "type": "boolean",
                    "description": "Is there visible bleeding?"
                },
                "contact_phone": {
                    "type": "string",
                    "description": "Phone number for callback"
                }
            },
            "required": ["symptoms"]
        }
    },
    {
        "name": "triage_symptoms",
        "description": "Assess urgency of pet symptoms",
        "permission": "public",
        "module": "emergency",
        "parameters": {
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of symptoms"
                },
                "species": {
                    "type": "string",
                    "description": "Type of animal"
                },
                "age": {
                    "type": "string",
                    "description": "Age of pet"
                }
            },
            "required": ["symptoms"]
        }
    },
    {
        "name": "get_first_aid",
        "description": "Get first aid instructions for a pet emergency",
        "permission": "public",
        "module": "emergency",
        "parameters": {
            "type": "object",
            "properties": {
                "emergency_type": {
                    "type": "string",
                    "description": "Type of emergency (poisoning, trauma, choking, etc.)"
                },
                "species": {
                    "type": "string",
                    "description": "Type of animal"
                }
            },
            "required": ["emergency_type"]
        }
    },
    {
        "name": "find_emergency_vet",
        "description": "Find emergency veterinary services",
        "permission": "public",
        "module": "emergency",
        "parameters": {
            "type": "object",
            "properties": {
                "include_24_hour": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include 24-hour emergency hospitals"
                }
            },
            "required": []
        }
    },
    {
        "name": "request_callback",
        "description": "Request emergency callback from veterinarian",
        "permission": "public",
        "module": "emergency",
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Phone number for callback"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["critical", "urgent", "can_wait"],
                    "description": "How urgent is the callback needed"
                },
                "notes": {
                    "type": "string",
                    "description": "Brief description of the issue"
                }
            },
            "required": ["phone"]
        }
    }
]
```

#### Tool Implementations
```python
from apps.ai_assistant.decorators import tool
from apps.vet_clinic.models import EmergencyCase, EmergencyProtocol, EmergencyContact
from apps.communications.tasks import send_emergency_alert


@tool(
    name="report_emergency",
    description="Report a pet emergency and get immediate guidance",
    permission="public",
    module="emergency"
)
def report_emergency(
    symptoms: str,
    pet_name: str = None,
    species: str = None,
    duration: str = None,
    is_conscious: bool = None,
    is_breathing: bool = None,
    is_bleeding: bool = None,
    contact_phone: str = None,
    context=None
) -> dict:
    """Report emergency and create case."""

    # Immediate critical assessment
    is_critical = False
    if is_breathing == False or is_conscious == False:
        is_critical = True

    # Match protocol based on symptoms
    protocol = _match_protocol(symptoms, species)

    # Determine triage level
    if is_critical:
        triage_level = 'critical'
    elif protocol:
        triage_level = protocol.triage_level
    else:
        triage_level = _assess_urgency(symptoms)

    # Create emergency case
    case = EmergencyCase.objects.create(
        pet_name=pet_name or 'Desconocido',
        pet_species=species or '',
        owner=context.user if context and context.user.is_authenticated else None,
        contact_phone=contact_phone or '',
        chief_complaint=symptoms,
        symptom_duration=duration or '',
        protocol=protocol,
        triage_level=triage_level,
        source='ai_chat',
        conversation_id=context.conversation_id if context else None
    )

    # Build response
    response = {
        "case_number": case.case_number,
        "triage_level": triage_level,
        "urgency_message": _get_urgency_message(triage_level),
    }

    # Add first aid if critical
    if is_critical or triage_level == 'critical':
        response["immediate_actions"] = [
            "Mantén la calma y habla suavemente a tu mascota",
            "No muevas al animal si hay trauma",
            "Mantén las vías respiratorias despejadas",
            "Ven inmediatamente a la clínica o llama al +52 998 316 2438"
        ]
        response["clinic_phone"] = "+52 998 316 2438"

        # Send alert to emergency contacts
        send_emergency_alert.delay(case.id)

    # Add protocol-specific instructions
    if protocol:
        response["first_aid"] = protocol.first_aid_instructions
        response["what_to_bring"] = protocol.what_to_bring
        response["what_not_to_do"] = protocol.what_not_to_do

    # Clinic status
    from apps.vet_clinic.services import ClinicService
    clinic_status = ClinicService().get_current_status()
    response["clinic_open"] = clinic_status['is_open']
    response["clinic_hours"] = clinic_status['hours_today']

    if not clinic_status['is_open']:
        response["after_hours_message"] = (
            "La clínica está cerrada. Para emergencias llama al "
            "+52 998 316 2438. Te contactaremos lo antes posible."
        )

    return response


@tool(
    name="triage_symptoms",
    description="Assess urgency of pet symptoms",
    permission="public",
    module="emergency"
)
def triage_symptoms(
    symptoms: list,
    species: str = None,
    age: str = None
) -> dict:
    """Assess symptom urgency."""

    # Critical symptoms that need immediate attention
    critical_symptoms = [
        'no respira', 'inconsciente', 'convulsiones', 'hemorragia',
        'atropellado', 'envenenamiento', 'asfixia', 'no puede orinar',
        'abdomen hinchado', 'colapso'
    ]

    urgent_symptoms = [
        'vómito sangre', 'diarrea sangre', 'no come', 'letárgico',
        'fiebre alta', 'dificultad respirar', 'cojea mucho',
        'herida profunda', 'ojo inflamado'
    ]

    symptoms_lower = [s.lower() for s in symptoms]
    symptoms_text = ' '.join(symptoms_lower)

    # Check for critical
    for critical in critical_symptoms:
        if critical in symptoms_text:
            return {
                "triage_level": "critical",
                "urgency": "CRÍTICO - Atención inmediata",
                "message": "Estos síntomas requieren atención veterinaria INMEDIATA. Llama al +52 998 316 2438 o ven directamente.",
                "action": "Ven a la clínica inmediatamente o llama para instrucciones"
            }

    # Check for urgent
    for urgent in urgent_symptoms:
        if urgent in symptoms_text:
            return {
                "triage_level": "urgent",
                "urgency": "URGENTE - Dentro de 1-2 horas",
                "message": "Estos síntomas son serios y requieren atención pronto.",
                "action": "Agenda una cita urgente o llama para más orientación"
            }

    # Semi-urgent for puppies/kittens or senior pets
    if age and ('cachorro' in age.lower() or 'gatito' in age.lower() or
                'senior' in age.lower() or 'viejo' in age.lower()):
        return {
            "triage_level": "semi_urgent",
            "urgency": "SEMI-URGENTE - Hoy si es posible",
            "message": "Por la edad de tu mascota, recomendamos revisión pronto.",
            "action": "Agenda una cita para hoy o mañana temprano"
        }

    return {
        "triage_level": "non_urgent",
        "urgency": "No urgente - Puede esperar",
        "message": "Los síntomas no parecen críticos, pero es bueno hacer una revisión.",
        "action": "Puedes agendar una cita regular cuando te convenga"
    }


@tool(
    name="get_first_aid",
    description="Get first aid instructions for a pet emergency",
    permission="public",
    module="emergency"
)
def get_first_aid(emergency_type: str, species: str = None) -> dict:
    """Get first aid instructions."""

    # Try to match protocol
    protocol = EmergencyProtocol.objects.filter(
        keywords__icontains=emergency_type,
        is_active=True
    ).first()

    if not protocol:
        # Fallback generic protocol
        protocol = EmergencyProtocol.objects.filter(
            slug='general-emergency',
            is_active=True
        ).first()

    if protocol:
        return {
            "emergency_type": protocol.name,
            "triage_level": protocol.triage_level,
            "first_aid": protocol.first_aid_instructions,
            "what_to_bring": protocol.what_to_bring,
            "what_not_to_do": protocol.what_not_to_do,
            "typical_treatment": protocol.typical_treatment,
            "estimated_cost": protocol.estimated_cost_range,
            "call_now": protocol.triage_level in ['critical', 'urgent'],
            "clinic_phone": "+52 998 316 2438"
        }

    return {
        "message": "No tengo instrucciones específicas para este tipo de emergencia.",
        "recommendation": "Por favor llama al +52 998 316 2438 para orientación.",
        "general_advice": [
            "Mantén la calma",
            "No des medicamentos sin consultar",
            "Mantén al animal cálido y quieto",
            "Ven a la clínica lo antes posible"
        ]
    }


@tool(
    name="find_emergency_vet",
    description="Find emergency veterinary services",
    permission="public",
    module="emergency"
)
def find_emergency_vet(include_24_hour: bool = True) -> dict:
    """Find emergency vet services."""

    from apps.vet_clinic.services import ClinicService
    from apps.vet_clinic.models import Specialist

    clinic_status = ClinicService().get_current_status()

    result = {
        "pet_friendly": {
            "name": "Pet-Friendly Veterinaria",
            "phone": "+52 998 316 2438",
            "whatsapp": "+52 998 316 2438",
            "address": "Puerto Morelos, Quintana Roo",
            "is_open": clinic_status['is_open'],
            "hours_today": clinic_status['hours_today'],
            "accepts_emergencies": True
        }
    }

    if include_24_hour:
        # Get referral hospitals
        hospitals = Specialist.objects.filter(
            specialty__icontains='emergencia',
            is_active=True
        ).values('name', 'phone', 'address', 'notes')

        result["emergency_hospitals"] = list(hospitals)

        # Add known 24-hour options
        result["24_hour_options"] = [
            {
                "name": "Hospital Veterinario Cancún",
                "phone": "+52 998 XXX XXXX",
                "location": "Cancún, ~30 min de Puerto Morelos",
                "note": "Emergencias 24 horas"
            }
        ]

    return result


def _match_protocol(symptoms: str, species: str = None) -> EmergencyProtocol:
    """Match symptoms to protocol."""
    symptoms_lower = symptoms.lower()

    protocols = EmergencyProtocol.objects.filter(is_active=True)

    for protocol in protocols:
        for keyword in protocol.keywords:
            if keyword.lower() in symptoms_lower:
                if species and protocol.applies_to_species:
                    if species.lower() in [s.lower() for s in protocol.applies_to_species]:
                        return protocol
                else:
                    return protocol

    return None


def _assess_urgency(symptoms: str) -> str:
    """Basic urgency assessment."""
    symptoms_lower = symptoms.lower()

    critical_words = ['sangre', 'no respira', 'inconsciente', 'convuls', 'veneno']
    urgent_words = ['vómito', 'diarrea', 'cojea', 'no come', 'dolor']

    for word in critical_words:
        if word in symptoms_lower:
            return 'critical'

    for word in urgent_words:
        if word in symptoms_lower:
            return 'urgent'

    return 'unknown'


def _get_urgency_message(level: str) -> str:
    """Get urgency message for triage level."""
    messages = {
        'critical': '🚨 EMERGENCIA CRÍTICA - Ven inmediatamente o llama al +52 998 316 2438',
        'urgent': '⚠️ URGENTE - Necesitas atención veterinaria pronto (1-2 horas)',
        'semi_urgent': '📋 SEMI-URGENTE - Agenda una cita para hoy si es posible',
        'non_urgent': '📅 NO URGENTE - Puedes agendar una cita regular',
        'unknown': '❓ Necesitamos más información para evaluar la urgencia'
    }
    return messages.get(level, messages['unknown'])
```

#### Emergency Alert Task
```python
from celery import shared_task


@shared_task
def send_emergency_alert(case_id: int):
    """Send alert to emergency contacts."""
    from apps.vet_clinic.models import EmergencyCase, EmergencyContact
    from apps.communications.services.sms import SMSService
    from apps.communications.services.whatsapp import WhatsAppService

    case = EmergencyCase.objects.get(id=case_id)

    # Get on-call contacts
    contacts = EmergencyContact.objects.filter(
        is_active=True,
        receives_critical=True
    ).order_by('priority')

    sms = SMSService()
    wa = WhatsAppService()

    message = (
        f"🚨 EMERGENCIA {case.case_number}\n"
        f"Paciente: {case.pet_name} ({case.pet_species})\n"
        f"Síntomas: {case.chief_complaint[:100]}\n"
        f"Nivel: {case.get_triage_level_display()}\n"
        f"Contacto: {case.contact_phone}"
    )

    for contact in contacts[:3]:  # Alert top 3 contacts
        if contact.whatsapp:
            wa.send_text(contact.whatsapp, message)
        elif contact.phone:
            sms.send(contact.phone, message)
```

### Test Cases
- [ ] report_emergency creates case
- [ ] Critical symptoms trigger alert
- [ ] Protocol matching works
- [ ] Triage assessment accurate
- [ ] First aid instructions returned
- [ ] Emergency contacts notified
- [ ] After-hours handling works

### Definition of Done
- [ ] All AI tools implemented
- [ ] Emergency alerts working
- [ ] Protocols seeded in database
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-050: Emergency Models
- T-010: Tool Calling Framework
- T-046: SMS Integration
- T-047: WhatsApp Integration

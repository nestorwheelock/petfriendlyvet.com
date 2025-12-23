"""Tool calling framework for AI assistant."""
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from executing a tool."""

    success: bool
    data: Any
    error: str | None = None
    ui_component: str | None = None

    def to_message(self) -> str:
        """Format result for AI context."""
        if self.success:
            return json.dumps(self.data)
        return f"Error: {self.error}"


@dataclass
class Tool:
    """Definition of an AI tool."""

    name: str
    description: str
    parameters: dict
    handler: Callable
    permission_level: str = 'public'  # public, customer, staff, admin
    module: str = 'core'

    def to_openai_format(self) -> dict:
        """Convert to OpenAI function calling format."""
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': self.parameters
            }
        }


class ToolRegistry:
    """Central registry for all AI tools."""

    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: Tool) -> None:
        """Register a tool."""
        cls._tools[tool.name] = tool

    @classmethod
    def get_tools(cls) -> list[Tool]:
        """Get all registered tools."""
        return list(cls._tools.values())

    @classmethod
    def get_tools_for_user(cls, user=None) -> list[Tool]:
        """Get tools available for user's permission level.

        Args:
            user: Django user object or None for anonymous

        Returns:
            List of Tool objects the user can access
        """
        if user is None or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            # Anonymous users get public tools only
            return [t for t in cls._tools.values() if t.permission_level == 'public']

        user_role = getattr(user, 'role', 'customer')

        # Define permission hierarchy
        role_levels = {
            'public': 0,
            'customer': 1,
            'staff': 2,
            'admin': 3,
        }

        user_level = role_levels.get(user_role, 1)

        # Return tools at or below user's permission level
        return [
            t for t in cls._tools.values()
            if role_levels.get(t.permission_level, 0) <= user_level
        ]

    @classmethod
    def execute(cls, tool_name: str, params: dict, context: dict) -> ToolResult:
        """Execute a tool with given parameters.

        Args:
            tool_name: Name of the tool to execute
            params: Parameters to pass to the tool
            context: Execution context (user, language, etc.)

        Returns:
            ToolResult with success/failure and data
        """
        tool = cls._tools.get(tool_name)

        if tool is None:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found"
            )

        try:
            result = tool.handler(**params)
            return ToolResult(success=True, data=result)
        except Exception as e:
            logger.exception("Tool execution error for '%s'", tool_name)
            return ToolResult(
                success=False,
                data=None,
                error="Tool execution failed. Please try again."
            )

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (for testing)."""
        cls._tools.clear()


def tool(
    name: str,
    description: str,
    parameters: dict = None,
    permission: str = 'public',
    module: str = 'core'
):
    """Decorator to register a function as a tool.

    Args:
        name: Tool name for AI to call
        description: Description for AI context
        parameters: JSON Schema for parameters
        permission: Required permission level
        module: Django app providing this tool

    Usage:
        @tool(
            name='get_clinic_hours',
            description='Get clinic operating hours',
            permission='public'
        )
        def get_clinic_hours(day: str = None) -> dict:
            return {'hours': '9am-8pm'}
    """
    if parameters is None:
        parameters = {'type': 'object', 'properties': {}}

    def decorator(func: Callable) -> Callable:
        t = Tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=func,
            permission_level=permission,
            module=module
        )
        ToolRegistry.register(t)
        return func

    return decorator


async def handle_tool_calls(
    tool_calls: list[dict],
    context: dict
) -> list[dict]:
    """Execute multiple tool calls and return results.

    Args:
        tool_calls: List of tool call dicts from AI
        context: Execution context

    Returns:
        List of result dicts for AI context
    """
    results = []
    for call in tool_calls:
        func_data = call.get('function', {})
        tool_name = func_data.get('name', '')
        arguments = func_data.get('arguments', '{}')

        try:
            params = json.loads(arguments)
        except json.JSONDecodeError:
            params = {}

        result = ToolRegistry.execute(tool_name, params, context)
        results.append({
            'tool_call_id': call.get('id', ''),
            'role': 'tool',
            'content': result.to_message()
        })

    return results


# =============================================================================
# Built-in Tools for Pet-Friendly Vet
# =============================================================================

@tool(
    name='get_clinic_hours',
    description='Get the clinic operating hours for a specific day or all days',
    parameters={
        'type': 'object',
        'properties': {
            'day': {
                'type': 'string',
                'description': 'Day of the week (monday, tuesday, etc.) or "all"',
                'enum': ['monday', 'tuesday', 'wednesday', 'thursday',
                         'friday', 'saturday', 'sunday', 'all']
            }
        },
        'required': []
    },
    permission='public',
    module='core'
)
def get_clinic_hours(day: str = 'all') -> dict:
    """Return clinic hours."""
    hours = {
        'monday': 'Closed',
        'tuesday': '9:00 AM - 8:00 PM',
        'wednesday': '9:00 AM - 8:00 PM',
        'thursday': '9:00 AM - 8:00 PM',
        'friday': '9:00 AM - 8:00 PM',
        'saturday': '9:00 AM - 8:00 PM',
        'sunday': '9:00 AM - 8:00 PM',
    }

    if day == 'all':
        return {'hours': hours}

    day_lower = day.lower()
    if day_lower in hours:
        return {'day': day, 'hours': hours[day_lower]}

    return {'error': f'Unknown day: {day}'}


@tool(
    name='get_services',
    description='Get list of clinic services by category',
    parameters={
        'type': 'object',
        'properties': {
            'category': {
                'type': 'string',
                'description': 'Service category',
                'enum': ['clinic', 'pharmacy', 'store', 'all']
            }
        },
        'required': []
    },
    permission='public',
    module='core'
)
def get_services(category: str = 'all') -> dict:
    """Return list of services."""
    services = {
        'clinic': [
            'General Consultation',
            'Vaccination',
            'Surgery',
            'Dental Care',
            'Laboratory',
            'Emergency Care',
        ],
        'pharmacy': [
            'Prescription Medications',
            'Flea & Tick Prevention',
            'Supplements',
            'Specialty Diets',
        ],
        'store': [
            'Pet Food',
            'Accessories',
            'Toys',
            'Grooming Supplies',
        ],
    }

    if category == 'all':
        return {'services': services}

    cat_lower = category.lower()
    if cat_lower in services:
        return {'category': category, 'services': services[cat_lower]}

    return {'error': f'Unknown category: {category}'}


@tool(
    name='get_contact_info',
    description='Get clinic contact information',
    parameters={'type': 'object', 'properties': {}},
    permission='public',
    module='core'
)
def get_contact_info() -> dict:
    """Return clinic contact info."""
    return {
        'name': 'Pet-Friendly Veterinary Clinic',
        'phone': '+52 998 316 2438',
        'whatsapp': 'https://wa.me/529983162438',
        'address': 'Puerto Morelos, Quintana Roo, Mexico',
        'email': 'contact@petfriendlyvet.com'
    }


# =============================================================================
# Pet Tools
# =============================================================================

@tool(
    name='list_user_pets',
    description='List all pets owned by a user',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user whose pets to list'
            }
        },
        'required': ['user_id']
    },
    permission='customer',
    module='pets'
)
def list_user_pets(user_id: int) -> dict:
    """Return list of pets owned by user."""
    from django.contrib.auth import get_user_model
    from apps.pets.models import Pet

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    pets = Pet.objects.filter(owner=user).values(
        'id', 'name', 'species', 'breed', 'gender', 'date_of_birth'
    )

    pet_list = []
    for pet in pets:
        pet_data = {
            'id': pet['id'],
            'name': pet['name'],
            'species': pet['species'],
            'breed': pet['breed'] or '',
            'gender': pet['gender'],
        }
        if pet['date_of_birth']:
            pet_data['date_of_birth'] = pet['date_of_birth'].isoformat()
        pet_list.append(pet_data)

    return {'pets': pet_list}


@tool(
    name='get_pet_profile',
    description='Get detailed profile for a specific pet',
    parameters={
        'type': 'object',
        'properties': {
            'pet_id': {
                'type': 'integer',
                'description': 'The ID of the pet'
            },
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user (for ownership verification)'
            }
        },
        'required': ['pet_id', 'user_id']
    },
    permission='customer',
    module='pets'
)
def get_pet_profile(pet_id: int, user_id: int) -> dict:
    """Return detailed pet profile."""
    from apps.pets.models import Pet

    try:
        pet = Pet.objects.get(id=pet_id)
    except Pet.DoesNotExist:
        return {'error': f'Pet with ID {pet_id} not found'}

    if pet.owner_id != user_id:
        return {'error': 'Access denied. This pet belongs to another user.'}

    profile = {
        'id': pet.id,
        'name': pet.name,
        'species': pet.species,
        'breed': pet.breed or '',
        'gender': pet.gender,
        'age_years': pet.age_years,
        'weight_kg': float(pet.weight_kg) if pet.weight_kg else None,
        'microchip_id': pet.microchip_id or '',
        'is_neutered': pet.is_neutered,
    }

    if pet.date_of_birth:
        profile['date_of_birth'] = pet.date_of_birth.isoformat()

    return profile


@tool(
    name='get_vaccination_status',
    description='Get vaccination status and upcoming due dates for a pet',
    parameters={
        'type': 'object',
        'properties': {
            'pet_id': {
                'type': 'integer',
                'description': 'The ID of the pet'
            },
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user (for ownership verification)'
            }
        },
        'required': ['pet_id', 'user_id']
    },
    permission='customer',
    module='pets'
)
def get_vaccination_status(pet_id: int, user_id: int) -> dict:
    """Return vaccination status for a pet."""
    from apps.pets.models import Pet, Vaccination

    try:
        pet = Pet.objects.get(id=pet_id)
    except Pet.DoesNotExist:
        return {'error': f'Pet with ID {pet_id} not found'}

    if pet.owner_id != user_id:
        return {'error': 'Access denied. This pet belongs to another user.'}

    vaccinations = Vaccination.objects.filter(pet=pet).order_by('-date_administered')

    vax_list = []
    for vax in vaccinations:
        vax_data = {
            'id': vax.id,
            'vaccine_name': vax.vaccine_name,
            'date_administered': vax.date_administered.isoformat(),
            'next_due_date': vax.next_due_date.isoformat() if vax.next_due_date else None,
            'is_overdue': vax.is_overdue,
            'is_due_soon': vax.is_due_soon,
        }
        vax_list.append(vax_data)

    return {
        'pet_name': pet.name,
        'pet_id': pet.id,
        'vaccinations': vax_list
    }


# =============================================================================
# Appointment Tools
# =============================================================================

@tool(
    name='list_services',
    description='List available clinic services, optionally filtered by category',
    parameters={
        'type': 'object',
        'properties': {
            'category': {
                'type': 'string',
                'description': 'Service category to filter by',
                'enum': ['clinic', 'grooming', 'lab', 'surgery', 'dental',
                         'emergency', 'other', 'all']
            }
        },
        'required': []
    },
    permission='public',
    module='appointments'
)
def list_services(category: str = 'all') -> dict:
    """Return list of available services."""
    from apps.appointments.models import ServiceType

    services = ServiceType.objects.filter(is_active=True)

    if category and category != 'all':
        services = services.filter(category=category)

    service_list = []
    for svc in services:
        service_list.append({
            'id': svc.id,
            'name': svc.name,
            'description': svc.description,
            'duration_minutes': svc.duration_minutes,
            'price': str(svc.price),
            'category': svc.category,
            'requires_pet': svc.requires_pet
        })

    return {'services': service_list}


@tool(
    name='check_availability',
    description='Check available appointment slots for a given date and service',
    parameters={
        'type': 'object',
        'properties': {
            'service_id': {
                'type': 'integer',
                'description': 'The ID of the service type'
            },
            'date': {
                'type': 'string',
                'description': 'Date to check availability (YYYY-MM-DD format)'
            },
            'staff_id': {
                'type': 'integer',
                'description': 'Optional staff member ID to filter by'
            }
        },
        'required': ['service_id', 'date']
    },
    permission='public',
    module='appointments'
)
def check_availability(
    service_id: int,
    date: str,
    staff_id: int = None
) -> dict:
    """Return available time slots for a given date."""
    from datetime import datetime
    from django.contrib.auth import get_user_model
    from apps.appointments.models import ServiceType
    from apps.appointments.services import AvailabilityService

    User = get_user_model()

    try:
        service = ServiceType.objects.get(id=service_id)
    except ServiceType.DoesNotExist:
        return {'error': f'Service with ID {service_id} not found'}

    try:
        check_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return {'error': 'Invalid date format. Use YYYY-MM-DD'}

    staff = None
    if staff_id:
        try:
            staff = User.objects.get(id=staff_id)
        except User.DoesNotExist:
            return {'error': f'Staff member with ID {staff_id} not found'}

    slots = AvailabilityService.get_available_slots(
        date=check_date,
        service=service,
        staff=staff
    )

    # Format slots for response
    slot_list = []
    for slot in slots:
        slot_list.append({
            'time': slot['time'].strftime('%H:%M'),
            'staff_id': slot['staff_id']
        })

    return {
        'date': date,
        'service_id': service_id,
        'service_name': service.name,
        'slots': slot_list
    }


@tool(
    name='book_appointment',
    description='Book an appointment for a pet',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the pet owner'
            },
            'pet_id': {
                'type': 'integer',
                'description': 'The ID of the pet (optional for some services)'
            },
            'service_id': {
                'type': 'integer',
                'description': 'The ID of the service type'
            },
            'staff_id': {
                'type': 'integer',
                'description': 'The ID of the staff member/veterinarian'
            },
            'date': {
                'type': 'string',
                'description': 'Appointment date (YYYY-MM-DD format)'
            },
            'time': {
                'type': 'string',
                'description': 'Appointment time (HH:MM format)'
            },
            'notes': {
                'type': 'string',
                'description': 'Optional notes for the appointment'
            }
        },
        'required': ['user_id', 'service_id', 'staff_id', 'date', 'time']
    },
    permission='customer',
    module='appointments'
)
def book_appointment(
    user_id: int,
    service_id: int,
    staff_id: int,
    date: str,
    time: str,
    pet_id: int = None,
    notes: str = ''
) -> dict:
    """Book an appointment."""
    from datetime import datetime, time as time_type
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from apps.pets.models import Pet
    from apps.appointments.models import ServiceType
    from apps.appointments.services import AvailabilityService

    User = get_user_model()

    try:
        owner = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    try:
        service = ServiceType.objects.get(id=service_id)
    except ServiceType.DoesNotExist:
        return {'error': f'Service with ID {service_id} not found'}

    try:
        staff = User.objects.get(id=staff_id)
    except User.DoesNotExist:
        return {'error': f'Staff member with ID {staff_id} not found'}

    pet = None
    if pet_id:
        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return {'error': f'Pet with ID {pet_id} not found'}

        if pet.owner_id != user_id:
            return {'error': 'Access denied. This pet belongs to another user.'}

    try:
        appt_date = datetime.strptime(date, '%Y-%m-%d').date()
        appt_time = datetime.strptime(time, '%H:%M').time()
    except ValueError:
        return {'error': 'Invalid date or time format. Use YYYY-MM-DD and HH:MM'}

    start_datetime = timezone.make_aware(
        datetime.combine(appt_date, appt_time)
    )

    try:
        appointment = AvailabilityService.book_appointment(
            owner=owner,
            pet=pet,
            service=service,
            staff=staff,
            start_time=start_datetime,
            notes=notes
        )
    except ValueError as e:
        return {'error': str(e)}

    return {
        'appointment_id': appointment.id,
        'confirmation': f'Appointment booked for {appointment.scheduled_start.strftime("%B %d, %Y at %I:%M %p")}',
        'status': appointment.status,
        'pet_name': pet.name if pet else None,
        'service_name': service.name,
        'veterinarian': staff.get_full_name() or staff.username
    }


@tool(
    name='list_user_appointments',
    description='List appointments for a user',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user'
            },
            'status': {
                'type': 'string',
                'description': 'Filter by status',
                'enum': ['scheduled', 'confirmed', 'in_progress',
                         'completed', 'cancelled', 'no_show']
            },
            'upcoming_only': {
                'type': 'boolean',
                'description': 'Only show future appointments'
            }
        },
        'required': ['user_id']
    },
    permission='customer',
    module='appointments'
)
def list_user_appointments(
    user_id: int,
    status: str = None,
    upcoming_only: bool = False
) -> dict:
    """Return list of user's appointments."""
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from apps.appointments.models import Appointment

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    appointments = Appointment.objects.filter(owner=user)

    if status:
        appointments = appointments.filter(status=status)

    if upcoming_only:
        appointments = appointments.filter(scheduled_start__gte=timezone.now())

    appointments = appointments.order_by('scheduled_start')

    appt_list = []
    for appt in appointments:
        appt_data = {
            'id': appt.id,
            'pet_name': appt.pet.name if appt.pet else None,
            'service_name': appt.service.name,
            'scheduled_start': appt.scheduled_start.isoformat(),
            'scheduled_end': appt.scheduled_end.isoformat(),
            'status': appt.status,
            'veterinarian': (
                appt.veterinarian.get_full_name() or appt.veterinarian.username
            ) if appt.veterinarian else None
        }
        appt_list.append(appt_data)

    return {'appointments': appt_list}


@tool(
    name='cancel_appointment',
    description='Cancel an appointment',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user requesting cancellation'
            },
            'appointment_id': {
                'type': 'integer',
                'description': 'The ID of the appointment to cancel'
            },
            'reason': {
                'type': 'string',
                'description': 'Reason for cancellation'
            }
        },
        'required': ['user_id', 'appointment_id']
    },
    permission='customer',
    module='appointments'
)
def cancel_appointment(
    user_id: int,
    appointment_id: int,
    reason: str = ''
) -> dict:
    """Cancel an appointment."""
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from apps.appointments.models import Appointment

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        return {'error': f'Appointment with ID {appointment_id} not found'}

    if appointment.owner_id != user_id:
        return {'error': 'Access denied. This appointment belongs to another user.'}

    if appointment.status in ['completed', 'cancelled']:
        return {
            'error': f'Cannot cancel appointment with status: {appointment.status}'
        }

    appointment.status = 'cancelled'
    appointment.cancellation_reason = reason
    appointment.cancelled_at = timezone.now()
    appointment.save()

    return {
        'success': True,
        'message': 'Appointment cancelled successfully',
        'appointment_id': appointment.id
    }

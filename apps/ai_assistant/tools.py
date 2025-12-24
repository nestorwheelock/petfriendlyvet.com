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
    def get_tool(cls, name: str) -> Tool | None:
        """Get a specific tool by name.

        Args:
            name: Name of the tool to retrieve

        Returns:
            Tool object if found, None otherwise
        """
        return cls._tools.get(name)

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


# =============================================================================
# Store/E-Commerce Tools
# =============================================================================

@tool(
    name='search_products',
    description='Search for products in the store by name, category, or species',
    parameters={
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'Search query for product name or description'
            },
            'category': {
                'type': 'string',
                'description': 'Category slug to filter by'
            },
            'species': {
                'type': 'string',
                'description': 'Pet species to filter products for (dog, cat, bird, etc.)'
            },
            'max_price': {
                'type': 'number',
                'description': 'Maximum price filter'
            },
            'in_stock_only': {
                'type': 'boolean',
                'description': 'Only show products in stock'
            }
        },
        'required': []
    },
    permission='public',
    module='store'
)
def search_products(
    query: str = None,
    category: str = None,
    species: str = None,
    max_price: float = None,
    in_stock_only: bool = True
) -> dict:
    """Search for products in the store."""
    from django.db.models import Q
    from apps.store.models import Product, Category

    products = Product.objects.filter(is_active=True)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(name_es__icontains=query) |
            Q(description__icontains=query)
        )

    if category:
        try:
            cat = Category.objects.get(slug=category)
            products = products.filter(category=cat)
        except Category.DoesNotExist:
            pass

    if species:
        # Manual filtering for SQLite compatibility
        product_pks = [
            p.pk for p in products
            if species.lower() in [s.lower() for s in p.suitable_for_species]
        ]
        products = products.filter(pk__in=product_pks)

    if max_price:
        products = products.filter(price__lte=max_price)

    if in_stock_only:
        products = products.filter(stock_quantity__gt=0)

    products = products[:20]  # Limit results

    product_list = []
    for p in products:
        product_list.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'price': str(p.price),
            'compare_at_price': str(p.compare_at_price) if p.compare_at_price else None,
            'is_in_stock': p.is_in_stock,
            'is_on_sale': p.is_on_sale,
            'category': p.category.name,
            'suitable_for': p.suitable_for_species
        })

    return {'products': product_list, 'count': len(product_list)}


@tool(
    name='get_product_details',
    description='Get detailed information about a specific product',
    parameters={
        'type': 'object',
        'properties': {
            'product_id': {
                'type': 'integer',
                'description': 'The ID of the product'
            },
            'slug': {
                'type': 'string',
                'description': 'The slug of the product (alternative to product_id)'
            }
        },
        'required': []
    },
    permission='public',
    module='store'
)
def get_product_details(product_id: int = None, slug: str = None) -> dict:
    """Get detailed product information."""
    from apps.store.models import Product

    if not product_id and not slug:
        return {'error': 'Either product_id or slug is required'}

    try:
        if product_id:
            product = Product.objects.get(id=product_id, is_active=True)
        else:
            product = Product.objects.get(slug=slug, is_active=True)
    except Product.DoesNotExist:
        return {'error': 'Product not found'}

    return {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'description': product.description,
        'price': str(product.price),
        'compare_at_price': str(product.compare_at_price) if product.compare_at_price else None,
        'discount_percentage': product.discount_percentage,
        'sku': product.sku,
        'is_in_stock': product.is_in_stock,
        'is_low_stock': product.is_low_stock,
        'stock_quantity': product.stock_quantity,
        'category': product.category.name,
        'category_slug': product.category.slug,
        'suitable_for_species': product.suitable_for_species,
        'suitable_for_sizes': product.suitable_for_sizes,
        'suitable_for_ages': product.suitable_for_ages,
        'weight_kg': float(product.weight_kg) if product.weight_kg else None
    }


@tool(
    name='get_store_categories',
    description='Get list of product categories in the store',
    parameters={
        'type': 'object',
        'properties': {
            'include_product_count': {
                'type': 'boolean',
                'description': 'Include count of products in each category'
            }
        },
        'required': []
    },
    permission='public',
    module='store'
)
def get_store_categories(include_product_count: bool = False) -> dict:
    """Get list of product categories."""
    from apps.store.models import Category

    categories = Category.objects.filter(is_active=True, parent__isnull=True)

    category_list = []
    for cat in categories:
        cat_data = {
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'description': cat.description
        }

        if include_product_count:
            cat_data['product_count'] = cat.products.filter(is_active=True).count()

        # Include subcategories
        children = cat.children.filter(is_active=True)
        if children.exists():
            cat_data['subcategories'] = [
                {'id': c.id, 'name': c.name, 'slug': c.slug}
                for c in children
            ]

        category_list.append(cat_data)

    return {'categories': category_list}


@tool(
    name='get_user_cart',
    description='Get the current shopping cart for a user',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user'
            }
        },
        'required': ['user_id']
    },
    permission='customer',
    module='store'
)
def get_user_cart(user_id: int) -> dict:
    """Get user's shopping cart."""
    from django.contrib.auth import get_user_model
    from apps.store.models import Cart

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    cart, _ = Cart.objects.get_or_create(user=user)

    items = []
    for item in cart.items.all():
        items.append({
            'product_id': item.product.id,
            'product_name': item.product.name,
            'product_slug': item.product.slug,
            'quantity': item.quantity,
            'unit_price': str(item.product.price),
            'subtotal': str(item.subtotal),
            'is_in_stock': item.product.is_in_stock,
            'stock_available': item.product.stock_quantity
        })

    return {
        'cart_id': cart.id,
        'item_count': cart.item_count,
        'total': str(cart.total),
        'items': items
    }


@tool(
    name='add_product_to_cart',
    description='Add a product to the user shopping cart',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user'
            },
            'product_id': {
                'type': 'integer',
                'description': 'The ID of the product to add'
            },
            'quantity': {
                'type': 'integer',
                'description': 'Quantity to add (default 1)'
            }
        },
        'required': ['user_id', 'product_id']
    },
    permission='customer',
    module='store'
)
def add_product_to_cart(user_id: int, product_id: int, quantity: int = 1) -> dict:
    """Add a product to the cart."""
    from django.contrib.auth import get_user_model
    from apps.store.models import Cart, Product

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return {'error': f'Product with ID {product_id} not found'}

    if product.track_inventory and product.stock_quantity < quantity:
        return {
            'error': f'Not enough stock. Only {product.stock_quantity} available.'
        }

    cart, _ = Cart.objects.get_or_create(user=user)
    cart.add_item(product, quantity)

    return {
        'success': True,
        'message': f'Added {quantity}x {product.name} to cart',
        'cart_total': str(cart.total),
        'cart_item_count': cart.item_count
    }


@tool(
    name='get_user_orders',
    description='Get order history for a user',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user'
            },
            'status': {
                'type': 'string',
                'description': 'Filter by order status',
                'enum': ['pending', 'paid', 'preparing', 'ready',
                         'shipped', 'delivered', 'cancelled', 'refunded']
            },
            'limit': {
                'type': 'integer',
                'description': 'Maximum number of orders to return'
            }
        },
        'required': ['user_id']
    },
    permission='customer',
    module='store'
)
def get_user_orders(
    user_id: int,
    status: str = None,
    limit: int = 10
) -> dict:
    """Get user's order history."""
    from django.contrib.auth import get_user_model
    from apps.store.models import Order

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    orders = Order.objects.filter(user=user).order_by('-created_at')

    if status:
        orders = orders.filter(status=status)

    orders = orders[:limit]

    order_list = []
    for order in orders:
        order_list.append({
            'id': order.id,
            'order_number': order.order_number,
            'status': order.status,
            'status_display': order.get_status_display(),
            'payment_method': order.payment_method,
            'payment_method_display': order.get_payment_method_display(),
            'fulfillment_method': order.fulfillment_method,
            'total': str(order.total),
            'item_count': order.items.count(),
            'created_at': order.created_at.isoformat(),
            'paid_at': order.paid_at.isoformat() if order.paid_at else None
        })

    return {'orders': order_list, 'count': len(order_list)}


@tool(
    name='get_order_details',
    description='Get detailed information about a specific order',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user (for ownership verification)'
            },
            'order_number': {
                'type': 'string',
                'description': 'The order number'
            }
        },
        'required': ['user_id', 'order_number']
    },
    permission='customer',
    module='store'
)
def get_order_details(user_id: int, order_number: str) -> dict:
    """Get detailed order information."""
    from django.contrib.auth import get_user_model
    from apps.store.models import Order

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        return {'error': f'Order {order_number} not found'}

    if order.user_id != user_id:
        return {'error': 'Access denied. This order belongs to another user.'}

    items = []
    for item in order.items.all():
        items.append({
            'product_name': item.product_name,
            'sku': item.product_sku,
            'quantity': item.quantity,
            'unit_price': str(item.price),
            'subtotal': str(item.subtotal)
        })

    return {
        'order_number': order.order_number,
        'status': order.status,
        'status_display': order.get_status_display(),
        'payment_method': order.payment_method,
        'payment_method_display': order.get_payment_method_display(),
        'fulfillment_method': order.fulfillment_method,
        'fulfillment_display': order.get_fulfillment_method_display(),
        'subtotal': str(order.subtotal),
        'tax': str(order.tax),
        'shipping_cost': str(order.shipping_cost),
        'discount_amount': str(order.discount_amount),
        'total': str(order.total),
        'items': items,
        'shipping_name': order.shipping_name,
        'shipping_address': order.shipping_address,
        'shipping_phone': order.shipping_phone,
        'created_at': order.created_at.isoformat(),
        'paid_at': order.paid_at.isoformat() if order.paid_at else None,
        'notes': order.notes
    }


@tool(
    name='get_product_recommendations',
    description='Get product recommendations based on pet profile or purchase history',
    parameters={
        'type': 'object',
        'properties': {
            'pet_id': {
                'type': 'integer',
                'description': 'The ID of the pet to get recommendations for'
            },
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user (for ownership verification)'
            },
            'category': {
                'type': 'string',
                'description': 'Category to filter recommendations'
            }
        },
        'required': ['pet_id', 'user_id']
    },
    permission='customer',
    module='store'
)
def get_product_recommendations(
    pet_id: int,
    user_id: int,
    category: str = None
) -> dict:
    """Get product recommendations for a pet."""
    from apps.pets.models import Pet
    from apps.store.models import Product, Category

    try:
        pet = Pet.objects.get(id=pet_id)
    except Pet.DoesNotExist:
        return {'error': f'Pet with ID {pet_id} not found'}

    if pet.owner_id != user_id:
        return {'error': 'Access denied. This pet belongs to another user.'}

    products = Product.objects.filter(is_active=True, stock_quantity__gt=0)

    if category:
        try:
            cat = Category.objects.get(slug=category)
            products = products.filter(category=cat)
        except Category.DoesNotExist:
            pass

    # Filter by species
    species = pet.species.lower()
    product_pks = [
        p.pk for p in products
        if species in [s.lower() for s in p.suitable_for_species] or not p.suitable_for_species
    ]
    products = products.filter(pk__in=product_pks)

    # Prioritize featured products
    products = products.order_by('-is_featured', '-created_at')[:10]

    recommendations = []
    for p in products:
        recommendations.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'price': str(p.price),
            'is_on_sale': p.is_on_sale,
            'discount_percentage': p.discount_percentage if p.is_on_sale else 0,
            'category': p.category.name,
            'reason': f'Great for {pet.species.lower()}s like {pet.name}'
        })

    return {
        'pet_name': pet.name,
        'pet_species': pet.species,
        'recommendations': recommendations
    }


# =============================================================================
# Pharmacy Tools
# =============================================================================

@tool(
    name='get_pet_prescriptions',
    description='Get active prescriptions for a pet',
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
            },
            'include_expired': {
                'type': 'boolean',
                'description': 'Include expired prescriptions'
            }
        },
        'required': ['pet_id', 'user_id']
    },
    permission='customer',
    module='pharmacy'
)
def get_pet_prescriptions(
    pet_id: int,
    user_id: int,
    include_expired: bool = False
) -> dict:
    """Get prescriptions for a pet."""
    from apps.pets.models import Pet
    from apps.pharmacy.models import Prescription

    try:
        pet = Pet.objects.get(id=pet_id)
    except Pet.DoesNotExist:
        return {'error': f'Pet with ID {pet_id} not found'}

    if pet.owner_id != user_id:
        return {'error': 'Access denied. This pet belongs to another user.'}

    prescriptions = Prescription.objects.filter(pet=pet)

    if not include_expired:
        prescriptions = prescriptions.filter(status='active')

    prescription_list = []
    for rx in prescriptions:
        prescription_list.append({
            'id': rx.id,
            'medication_name': rx.medication.name,
            'strength': rx.strength,
            'dosage': rx.dosage,
            'frequency': rx.frequency,
            'duration': rx.duration,
            'instructions': rx.instructions,
            'quantity': rx.quantity,
            'refills_remaining': rx.refills_remaining,
            'refills_authorized': rx.refills_authorized,
            'prescribed_date': rx.prescribed_date.isoformat(),
            'expiration_date': rx.expiration_date.isoformat(),
            'status': rx.status,
            'can_refill': rx.can_refill,
            'is_controlled': rx.medication.is_controlled
        })

    return {'prescriptions': prescription_list}


@tool(
    name='check_refill_eligibility',
    description='Check if a prescription can be refilled',
    parameters={
        'type': 'object',
        'properties': {
            'prescription_id': {
                'type': 'integer',
                'description': 'The ID of the prescription'
            },
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user (for ownership verification)'
            }
        },
        'required': ['prescription_id', 'user_id']
    },
    permission='customer',
    module='pharmacy'
)
def check_refill_eligibility(prescription_id: int, user_id: int) -> dict:
    """Check if a prescription can be refilled."""
    from apps.pharmacy.models import Prescription

    try:
        rx = Prescription.objects.get(id=prescription_id)
    except Prescription.DoesNotExist:
        return {'error': f'Prescription with ID {prescription_id} not found'}

    if rx.owner_id != user_id:
        return {'error': 'Access denied. This prescription belongs to another user.'}

    result = {
        'prescription_id': rx.id,
        'medication_name': rx.medication.name,
        'can_refill': rx.can_refill,
        'refills_remaining': rx.refills_remaining,
        'refills_authorized': rx.refills_authorized,
        'expiration_date': rx.expiration_date.isoformat(),
        'is_expired': rx.is_expired,
        'is_controlled': rx.medication.is_controlled
    }

    if not rx.can_refill:
        if rx.is_expired:
            result['reason'] = 'Prescription has expired'
        elif rx.refills_remaining == 0:
            result['reason'] = 'No refills remaining'
        elif rx.status != 'active':
            result['reason'] = f'Prescription status is {rx.status}'

    if rx.medication.is_controlled:
        result['reason'] = 'Controlled substances cannot be refilled online. Please call the pharmacy.'

    return result


@tool(
    name='request_refill',
    description='Request a prescription refill',
    parameters={
        'type': 'object',
        'properties': {
            'prescription_id': {
                'type': 'integer',
                'description': 'The ID of the prescription'
            },
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user'
            },
            'quantity': {
                'type': 'integer',
                'description': 'Quantity to request (optional, uses standard if not provided)'
            },
            'notes': {
                'type': 'string',
                'description': 'Notes for the refill request'
            }
        },
        'required': ['prescription_id', 'user_id']
    },
    permission='customer',
    module='pharmacy'
)
def request_refill(
    prescription_id: int,
    user_id: int,
    quantity: int = None,
    notes: str = ''
) -> dict:
    """Request a prescription refill."""
    from django.contrib.auth import get_user_model
    from apps.pharmacy.models import Prescription, RefillRequest

    User = get_user_model()

    try:
        rx = Prescription.objects.get(id=prescription_id)
    except Prescription.DoesNotExist:
        return {'error': f'Prescription with ID {prescription_id} not found'}

    if rx.owner_id != user_id:
        return {'error': 'Access denied. This prescription belongs to another user.'}

    # Cannot refill controlled substances online
    if rx.medication.is_controlled:
        return {
            'success': False,
            'error': 'Controlled substances cannot be refilled online. Please call or visit the pharmacy.'
        }

    if not rx.can_refill:
        if rx.is_expired:
            return {'success': False, 'error': 'Prescription has expired'}
        if rx.refills_remaining == 0:
            return {'success': False, 'error': 'No refills remaining'}
        return {'success': False, 'error': 'Prescription cannot be refilled'}

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    refill = RefillRequest.objects.create(
        prescription=rx,
        requested_by=user,
        quantity_requested=quantity,
        notes=notes
    )

    return {
        'success': True,
        'request_id': refill.id,
        'message': f'Refill requested for {rx.medication.name}',
        'prescription_id': rx.id,
        'medication_name': rx.medication.name,
        'quantity': quantity or rx.quantity
    }


@tool(
    name='get_medication_info',
    description='Get information about a medication',
    parameters={
        'type': 'object',
        'properties': {
            'medication_name': {
                'type': 'string',
                'description': 'Name of the medication to look up'
            },
            'species': {
                'type': 'string',
                'description': 'Species to filter for (optional)'
            }
        },
        'required': ['medication_name']
    },
    permission='public',
    module='pharmacy'
)
def get_medication_info(medication_name: str, species: str = None) -> dict:
    """Get information about a medication."""
    from django.db.models import Q
    from apps.pharmacy.models import Medication

    meds = Medication.objects.filter(
        Q(name__icontains=medication_name) |
        Q(generic_name__icontains=medication_name)
    )

    if species:
        # Filter by species (manual for SQLite compatibility)
        med_pks = [
            m.pk for m in meds
            if species.lower() in [s.lower() for s in m.species] or not m.species
        ]
        meds = meds.filter(pk__in=med_pks)

    if not meds.exists():
        return {'error': f'No medication found matching "{medication_name}"'}

    med = meds.first()

    return {
        'medication': {
            'id': med.id,
            'name': med.name,
            'generic_name': med.generic_name,
            'drug_class': med.drug_class,
            'is_controlled': med.is_controlled,
            'schedule': med.schedule,
            'requires_prescription': med.requires_prescription,
            'species': med.species,
            'dosage_forms': med.dosage_forms,
            'strengths': med.strengths,
            'contraindications': med.contraindications,
            'side_effects': med.side_effects,
            'warnings': med.warnings
        }
    }


@tool(
    name='get_refill_status',
    description='Get status of a refill request',
    parameters={
        'type': 'object',
        'properties': {
            'refill_request_id': {
                'type': 'integer',
                'description': 'The ID of the refill request'
            },
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user (for ownership verification)'
            }
        },
        'required': ['refill_request_id', 'user_id']
    },
    permission='customer',
    module='pharmacy'
)
def get_refill_status(refill_request_id: int, user_id: int) -> dict:
    """Get status of a refill request."""
    from apps.pharmacy.models import RefillRequest

    try:
        refill = RefillRequest.objects.get(id=refill_request_id)
    except RefillRequest.DoesNotExist:
        return {'error': f'Refill request with ID {refill_request_id} not found'}

    if refill.requested_by_id != user_id:
        return {'error': 'Access denied. This refill request belongs to another user.'}

    result = {
        'request_id': refill.id,
        'status': refill.status,
        'medication_name': refill.prescription.medication.name,
        'quantity_requested': refill.quantity_requested or refill.prescription.quantity,
        'requested_at': refill.created_at.isoformat(),
        'notes': refill.notes
    }

    if refill.status == 'denied':
        result['denial_reason'] = refill.denial_reason

    if refill.fill:
        result['fill_status'] = refill.fill.status
        if refill.fill.ready_at:
            result['ready_at'] = refill.fill.ready_at.isoformat()

    return result


@tool(
    name='get_pharmacy_queue',
    description='Get pending prescription orders (staff only)',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the staff user'
            },
            'status': {
                'type': 'string',
                'description': 'Filter by status (pending, processing, ready)',
                'enum': ['pending', 'approved', 'filled']
            }
        },
        'required': ['user_id']
    },
    permission='staff',
    module='pharmacy'
)
def get_pharmacy_queue(user_id: int, status: str = None) -> dict:
    """Get pharmacy queue (staff only)."""
    from django.contrib.auth import get_user_model
    from apps.pharmacy.models import RefillRequest

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    if not user.is_staff:
        return {'error': 'Access denied. Staff privileges required.'}

    requests = RefillRequest.objects.all().order_by('-created_at')

    if status:
        requests = requests.filter(status=status)
    else:
        requests = requests.filter(status__in=['pending', 'approved'])

    queue = []
    for req in requests[:50]:  # Limit to 50 items
        queue.append({
            'request_id': req.id,
            'status': req.status,
            'pet_name': req.prescription.pet.name,
            'owner_name': req.requested_by.get_full_name() or req.requested_by.username,
            'medication_name': req.prescription.medication.name,
            'strength': req.prescription.strength,
            'quantity': req.quantity_requested or req.prescription.quantity,
            'is_controlled': req.prescription.medication.is_controlled,
            'requested_at': req.created_at.isoformat(),
            'notes': req.notes
        })

    return {'queue': queue, 'count': len(queue)}


@tool(
    name='create_prescription',
    description='Create a new prescription (vet only)',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the prescribing vet'
            },
            'pet_id': {
                'type': 'integer',
                'description': 'The ID of the pet'
            },
            'medication_id': {
                'type': 'integer',
                'description': 'The ID of the medication'
            },
            'strength': {
                'type': 'string',
                'description': 'Medication strength (e.g., "5mg")'
            },
            'quantity': {
                'type': 'integer',
                'description': 'Quantity to dispense'
            },
            'dosage': {
                'type': 'string',
                'description': 'Dosage instructions (e.g., "1 tablet")'
            },
            'frequency': {
                'type': 'string',
                'description': 'Frequency (e.g., "twice daily")'
            },
            'duration': {
                'type': 'string',
                'description': 'Duration (e.g., "14 days")'
            },
            'refills': {
                'type': 'integer',
                'description': 'Number of refills authorized'
            },
            'instructions': {
                'type': 'string',
                'description': 'Additional instructions'
            }
        },
        'required': ['user_id', 'pet_id', 'medication_id', 'quantity', 'dosage', 'frequency']
    },
    permission='staff',
    module='pharmacy'
)
def create_prescription(
    user_id: int,
    pet_id: int,
    medication_id: int,
    quantity: int,
    dosage: str,
    frequency: str,
    strength: str = '',
    duration: str = '',
    refills: int = 0,
    instructions: str = ''
) -> dict:
    """Create a new prescription (vet only)."""
    from datetime import date, timedelta
    from apps.pets.models import Pet
    from apps.pharmacy.models import Medication, Prescription
    from apps.practice.models import StaffProfile

    try:
        staff = StaffProfile.objects.get(user_id=user_id)
    except StaffProfile.DoesNotExist:
        return {'error': 'Staff profile not found'}

    if not staff.can_prescribe:
        return {'error': 'Not authorized to prescribe medications'}

    try:
        pet = Pet.objects.get(id=pet_id)
    except Pet.DoesNotExist:
        return {'error': f'Pet with ID {pet_id} not found'}

    try:
        medication = Medication.objects.get(id=medication_id)
    except Medication.DoesNotExist:
        return {'error': f'Medication with ID {medication_id} not found'}

    # Controlled substances have limited refills
    if medication.is_controlled and refills > 0:
        if medication.schedule in ['II']:
            refills = 0  # Schedule II cannot have refills
        elif refills > 5:
            refills = 5  # Limit refills for controlled substances

    rx = Prescription.objects.create(
        pet=pet,
        owner=pet.owner,
        prescribing_vet=staff,
        medication=medication,
        strength=strength or (medication.strengths[0] if medication.strengths else ''),
        dosage_form=medication.dosage_forms[0] if medication.dosage_forms else 'tablet',
        quantity=quantity,
        dosage=dosage,
        frequency=frequency,
        duration=duration,
        instructions=instructions,
        refills_authorized=refills,
        refills_remaining=refills,
        prescribed_date=date.today(),
        expiration_date=date.today() + timedelta(days=180)  # 6 months default
    )

    return {
        'success': True,
        'prescription_id': rx.id,
        'message': f'Prescription created for {pet.name}: {medication.name} {strength}',
        'medication_name': medication.name,
        'is_controlled': medication.is_controlled
    }


# =============================================================================
# Billing Tools
# =============================================================================

@tool(
    name='get_invoice_details',
    description='Get details of a specific invoice',
    parameters={
        'type': 'object',
        'properties': {
            'invoice_id': {
                'type': 'integer',
                'description': 'The ID of the invoice'
            },
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user (for ownership verification)'
            }
        },
        'required': ['invoice_id', 'user_id']
    },
    permission='customer',
    module='billing'
)
def get_invoice_details(invoice_id: int, user_id: int) -> dict:
    """Get invoice details."""
    from apps.billing.models import Invoice

    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        return {'error': f'Invoice with ID {invoice_id} not found'}

    if invoice.owner_id != user_id:
        return {'error': 'Access denied. This invoice belongs to another user.'}

    items = []
    for item in invoice.items.all():
        items.append({
            'description': item.description,
            'quantity': str(item.quantity),
            'unit_price': str(item.unit_price),
            'discount_percent': str(item.discount_percent),
            'line_total': str(item.line_total)
        })

    return {
        'invoice': {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'status': invoice.status,
            'subtotal': str(invoice.subtotal),
            'discount_amount': str(invoice.discount_amount),
            'tax_amount': str(invoice.tax_amount),
            'total': str(invoice.total),
            'amount_paid': str(invoice.amount_paid),
            'balance_due': str(invoice.get_balance_due()),
            'due_date': invoice.due_date.isoformat(),
            'is_paid': invoice.is_paid,
            'is_overdue': invoice.is_overdue,
            'pet_name': invoice.pet.name if invoice.pet else None,
            'created_at': invoice.created_at.isoformat(),
            'items': items
        }
    }


@tool(
    name='get_customer_invoices',
    description='Get all invoices for a customer',
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
                'enum': ['draft', 'sent', 'paid', 'partial', 'overdue', 'cancelled']
            },
            'limit': {
                'type': 'integer',
                'description': 'Maximum number of invoices to return'
            }
        },
        'required': ['user_id']
    },
    permission='customer',
    module='billing'
)
def get_customer_invoices(
    user_id: int,
    status: str = None,
    limit: int = 20
) -> dict:
    """Get customer's invoices."""
    from django.contrib.auth import get_user_model
    from apps.billing.models import Invoice

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    invoices = Invoice.objects.filter(owner=user).order_by('-created_at')

    if status:
        invoices = invoices.filter(status=status)

    invoices = invoices[:limit]

    invoice_list = []
    for inv in invoices:
        invoice_list.append({
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'status': inv.status,
            'total': str(inv.total),
            'amount_paid': str(inv.amount_paid),
            'balance_due': str(inv.get_balance_due()),
            'due_date': inv.due_date.isoformat(),
            'is_paid': inv.is_paid,
            'is_overdue': inv.is_overdue,
            'pet_name': inv.pet.name if inv.pet else None,
            'created_at': inv.created_at.isoformat()
        })

    return {'invoices': invoice_list, 'count': len(invoice_list)}


@tool(
    name='check_coupon',
    description='Check if a coupon code is valid',
    parameters={
        'type': 'object',
        'properties': {
            'code': {
                'type': 'string',
                'description': 'The coupon code to check'
            }
        },
        'required': ['code']
    },
    permission='public',
    module='billing'
)
def check_coupon(code: str) -> dict:
    """Check if a coupon is valid."""
    from apps.billing.models import CouponCode

    try:
        coupon = CouponCode.objects.get(code=code)
    except CouponCode.DoesNotExist:
        return {'valid': False, 'error': 'Coupon code not found'}

    return {
        'valid': coupon.is_valid(),
        'code': coupon.code,
        'description': coupon.description,
        'discount_type': coupon.discount_type,
        'discount_value': str(coupon.discount_value),
        'minimum_purchase': str(coupon.minimum_purchase) if coupon.minimum_purchase else None,
        'valid_from': coupon.valid_from.isoformat(),
        'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
        'max_uses': coupon.max_uses,
        'times_used': coupon.times_used
    }


@tool(
    name='get_account_balance',
    description='Get account credit balance for a customer',
    parameters={
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': 'The ID of the user'
            }
        },
        'required': ['user_id']
    },
    permission='customer',
    module='billing'
)
def get_account_balance(user_id: int) -> dict:
    """Get customer's account credit balance."""
    from django.contrib.auth import get_user_model
    from apps.billing.models import AccountCredit

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {'error': f'User with ID {user_id} not found'}

    try:
        credit = AccountCredit.objects.get(owner=user)
        balance = str(credit.balance)
    except AccountCredit.DoesNotExist:
        balance = '0.00'

    return {
        'user_id': user_id,
        'balance': balance
    }


# =============================================================================
# Inventory Tools (S-024)
# =============================================================================

@tool(
    name='check_stock_level',
    description='Check current stock level for a product at a location',
    parameters={
        'type': 'object',
        'properties': {
            'product_id': {
                'type': 'integer',
                'description': 'The ID of the product'
            },
            'location': {
                'type': 'string',
                'description': 'Name of the stock location (optional)'
            }
        },
        'required': ['product_id']
    },
    permission='staff',
    module='inventory'
)
def check_stock_level(product_id: int, location: str = None) -> dict:
    """Check stock level for a product."""
    from apps.store.models import Product
    from apps.inventory.models import StockLevel, StockBatch, StockLocation

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return {'error': f'Product with ID {product_id} not found'}

    stock_levels = StockLevel.objects.filter(product=product)

    if location:
        try:
            loc = StockLocation.objects.get(name__icontains=location)
            stock_levels = stock_levels.filter(location=loc)
        except StockLocation.DoesNotExist:
            return {'error': f'Location "{location}" not found'}

    levels = []
    total_quantity = 0
    for level in stock_levels:
        batches = StockBatch.objects.filter(
            product=product,
            location=level.location,
            status='available',
            current_quantity__gt=0
        )
        batch_info = []
        for batch in batches:
            batch_info.append({
                'batch_number': batch.batch_number,
                'quantity': str(batch.current_quantity),
                'expiry_date': batch.expiry_date.isoformat() if batch.expiry_date else None,
                'days_until_expiry': batch.days_until_expiry
            })

        levels.append({
            'location': level.location.name,
            'location_type': level.location.location_type,
            'quantity': str(level.quantity),
            'available': str(level.available_quantity),
            'reserved': str(level.reserved_quantity),
            'is_below_minimum': level.is_below_minimum,
            'batches': batch_info
        })
        total_quantity += level.quantity

    return {
        'product_id': product_id,
        'product_name': product.name,
        'total_quantity': str(total_quantity),
        'locations': levels
    }


@tool(
    name='get_expiring_products',
    description='Get products expiring within a specified number of days',
    parameters={
        'type': 'object',
        'properties': {
            'days_ahead': {
                'type': 'integer',
                'description': 'Number of days to look ahead for expiring products'
            },
            'location': {
                'type': 'string',
                'description': 'Filter by location name (optional)'
            }
        },
        'required': ['days_ahead']
    },
    permission='staff',
    module='inventory'
)
def get_expiring_products(days_ahead: int, location: str = None) -> list:
    """Get products expiring within specified days."""
    from datetime import date, timedelta
    from apps.inventory.models import StockBatch, StockLocation

    cutoff_date = date.today() + timedelta(days=days_ahead)

    batches = StockBatch.objects.filter(
        expiry_date__lte=cutoff_date,
        expiry_date__gte=date.today(),
        status='available',
        current_quantity__gt=0
    ).select_related('product', 'location').order_by('expiry_date')

    if location:
        try:
            loc = StockLocation.objects.get(name__icontains=location)
            batches = batches.filter(location=loc)
        except StockLocation.DoesNotExist:
            return {'error': f'Location "{location}" not found'}

    expiring = []
    for batch in batches:
        expiring.append({
            'product_id': batch.product.id,
            'product_name': batch.product.name,
            'batch_number': batch.batch_number,
            'location': batch.location.name,
            'quantity': str(batch.current_quantity),
            'expiry_date': batch.expiry_date.isoformat(),
            'days_until_expiry': batch.days_until_expiry,
            'value': str(batch.current_quantity * batch.unit_cost)
        })

    return expiring


@tool(
    name='get_low_stock_products',
    description='Get products that are at or below their minimum stock level',
    parameters={
        'type': 'object',
        'properties': {
            'location': {
                'type': 'string',
                'description': 'Filter by location name (optional)'
            }
        },
        'required': []
    },
    permission='staff',
    module='inventory'
)
def get_low_stock_products(location: str = None) -> list:
    """Get products below minimum stock level."""
    from apps.inventory.models import StockLevel, StockLocation

    stock_levels = StockLevel.objects.select_related(
        'product', 'location'
    ).filter(quantity__gt=0)

    if location:
        try:
            loc = StockLocation.objects.get(name__icontains=location)
            stock_levels = stock_levels.filter(location=loc)
        except StockLocation.DoesNotExist:
            return {'error': f'Location "{location}" not found'}

    low_stock = []
    for level in stock_levels:
        if level.is_below_minimum:
            low_stock.append({
                'product_id': level.product.id,
                'product_name': level.product.name,
                'location': level.location.name,
                'current_quantity': str(level.quantity),
                'minimum_level': str(level.min_level or level.product.low_stock_threshold),
                'reorder_quantity': str(level.reorder_quantity) if level.reorder_quantity else None
            })

    return low_stock


# =============================================================================
# Referral Network Tools (S-025)
# =============================================================================

@tool(
    name='find_specialist',
    description='Find specialist veterinarians or facilities by specialty type',
    parameters={
        'type': 'object',
        'properties': {
            'specialty': {
                'type': 'string',
                'description': 'Specialty type (oncology, cardiology, surgery, emergency, etc.)'
            },
            'species': {
                'type': 'string',
                'description': 'Species to filter by (dog, cat, exotic, etc.)'
            },
            'urgent': {
                'type': 'boolean',
                'description': 'If true, prioritize 24-hour facilities'
            }
        },
        'required': ['specialty']
    },
    permission='staff',
    module='referrals'
)
def find_specialist(specialty: str, species: str = None, urgent: bool = False) -> dict:
    """Find specialists by specialty type and optional filters."""
    from apps.referrals.models import Specialist

    specialists = Specialist.objects.filter(
        is_active=True,
        specialty__icontains=specialty
    )

    if urgent:
        specialists = specialists.order_by('-is_24_hours', 'name')
    else:
        specialists = specialists.order_by('name')

    # Filter by species in Python to avoid JSONField contains lookup
    # which is not supported on SQLite
    if species:
        specialists = [s for s in specialists if species in (s.species_treated or [])]
    else:
        specialists = list(specialists)

    result = []
    for spec in specialists:
        result.append({
            'id': spec.id,
            'name': spec.name,
            'specialty': spec.specialty,
            'credentials': spec.credentials,
            'is_facility': spec.is_facility,
            'clinic_name': spec.clinic_name,
            'phone': spec.phone,
            'email': spec.email,
            'city': spec.city,
            'address': spec.address,
            'is_24_hours': spec.is_24_hours,
            'is_visiting': spec.is_visiting,
            'services': spec.services,
            'species_treated': spec.species_treated,
            'average_rating': str(spec.average_rating) if spec.average_rating else None,
            'total_referrals': spec.total_referrals_sent + spec.total_referrals_received
        })

    return {
        'success': True,
        'specialists': result,
        'count': len(result)
    }


@tool(
    name='get_visiting_schedule',
    description='Get schedule for visiting specialists at Pet-Friendly',
    parameters={
        'type': 'object',
        'properties': {
            'specialty': {
                'type': 'string',
                'description': 'Filter by specialist specialty'
            },
            'date_from': {
                'type': 'string',
                'description': 'Start date (YYYY-MM-DD)'
            },
            'date_to': {
                'type': 'string',
                'description': 'End date (YYYY-MM-DD)'
            }
        },
        'required': []
    },
    permission='staff',
    module='referrals'
)
def get_visiting_schedule(
    specialty: str = None,
    date_from: str = None,
    date_to: str = None
) -> dict:
    """Get upcoming visiting specialist schedules."""
    from datetime import datetime
    from django.utils import timezone
    from apps.referrals.models import VisitingSchedule

    schedules = VisitingSchedule.objects.select_related(
        'specialist'
    ).filter(status__in=['scheduled', 'confirmed'])

    # Default to upcoming 30 days
    if not date_from:
        start = timezone.now().date()
    else:
        start = datetime.strptime(date_from, '%Y-%m-%d').date()

    if not date_to:
        end = start + timezone.timedelta(days=30)
    else:
        end = datetime.strptime(date_to, '%Y-%m-%d').date()

    schedules = schedules.filter(date__gte=start, date__lte=end)

    if specialty:
        schedules = schedules.filter(
            specialist__specialty__icontains=specialty
        )

    result = []
    for sch in schedules:
        result.append({
            'id': sch.id,
            'specialist_id': sch.specialist.id,
            'specialist_name': sch.specialist.name,
            'specialty': sch.specialist.specialty,
            'date': str(sch.date),
            'start_time': str(sch.start_time),
            'end_time': str(sch.end_time),
            'services_available': sch.services_available,
            'max_appointments': sch.max_appointments,
            'appointments_booked': sch.appointments_booked,
            'slots_available': (sch.max_appointments or 0) - sch.appointments_booked,
            'status': sch.status
        })

    return {
        'success': True,
        'schedules': result,
        'count': len(result)
    }


@tool(
    name='create_referral',
    description='Create a referral to a specialist for a pet',
    parameters={
        'type': 'object',
        'properties': {
            'pet_id': {
                'type': 'integer',
                'description': 'ID of the pet being referred'
            },
            'specialist_id': {
                'type': 'integer',
                'description': 'ID of the specialist to refer to'
            },
            'reason': {
                'type': 'string',
                'description': 'Reason for the referral'
            },
            'urgency': {
                'type': 'string',
                'description': 'Urgency level (routine, urgent, emergency)',
                'enum': ['routine', 'urgent', 'emergency']
            },
            'services_requested': {
                'type': 'array',
                'items': {'type': 'string'},
                'description': 'List of services requested'
            },
            'clinical_summary': {
                'type': 'string',
                'description': 'Clinical summary for the specialist'
            }
        },
        'required': ['pet_id', 'specialist_id', 'reason']
    },
    permission='staff',
    module='referrals'
)
def create_referral(
    pet_id: int,
    specialist_id: int,
    reason: str,
    urgency: str = 'routine',
    services_requested: list = None,
    clinical_summary: str = None,
    user=None
) -> dict:
    """Create a new referral to a specialist."""
    from apps.pets.models import Pet
    from apps.referrals.models import Specialist, Referral

    try:
        pet = Pet.objects.get(pk=pet_id)
    except Pet.DoesNotExist:
        return {'success': False, 'message': f'Pet with ID {pet_id} not found'}

    try:
        specialist = Specialist.objects.get(pk=specialist_id)
    except Specialist.DoesNotExist:
        return {'success': False, 'message': f'Specialist with ID {specialist_id} not found'}

    referral = Referral.objects.create(
        direction='outbound',
        pet=pet,
        owner=pet.owner,
        specialist=specialist,
        reason=reason,
        urgency=urgency,
        requested_services=services_requested or [],
        clinical_summary=clinical_summary or '',
        status='draft',
        referred_by=user
    )

    return {
        'success': True,
        'referral_id': referral.id,
        'referral_number': referral.referral_number,
        'pet_name': pet.name,
        'specialist_name': specialist.name,
        'status': referral.status,
        'message': f'Referral created for {pet.name} to {specialist.name}'
    }


@tool(
    name='book_visiting_specialist',
    description='Book an appointment with a visiting specialist',
    parameters={
        'type': 'object',
        'properties': {
            'pet_id': {
                'type': 'integer',
                'description': 'ID of the pet'
            },
            'schedule_id': {
                'type': 'integer',
                'description': 'ID of the visiting schedule'
            },
            'service': {
                'type': 'string',
                'description': 'Service requested'
            },
            'reason': {
                'type': 'string',
                'description': 'Reason for the appointment'
            },
            'preferred_time': {
                'type': 'string',
                'description': 'Preferred time (HH:MM format)'
            }
        },
        'required': ['pet_id', 'schedule_id', 'service']
    },
    permission='staff',
    module='referrals'
)
def book_visiting_specialist(
    pet_id: int,
    schedule_id: int,
    service: str,
    reason: str = None,
    preferred_time: str = None,
    user=None
) -> dict:
    """Book an appointment with a visiting specialist."""
    from datetime import datetime, time
    from apps.pets.models import Pet
    from apps.referrals.models import VisitingSchedule, VisitingAppointment

    try:
        pet = Pet.objects.get(pk=pet_id)
    except Pet.DoesNotExist:
        return {'success': False, 'message': f'Pet with ID {pet_id} not found'}

    try:
        schedule = VisitingSchedule.objects.select_related('specialist').get(pk=schedule_id)
    except VisitingSchedule.DoesNotExist:
        return {'success': False, 'message': f'Schedule with ID {schedule_id} not found'}

    # Check capacity
    if schedule.max_appointments and schedule.appointments_booked >= schedule.max_appointments:
        return {
            'success': False,
            'message': 'Schedule is at full capacity. No slots available.'
        }

    # Parse preferred time or use schedule start time
    if preferred_time:
        try:
            appt_time = datetime.strptime(preferred_time, '%H:%M').time()
        except ValueError:
            appt_time = schedule.start_time
    else:
        appt_time = schedule.start_time

    appointment = VisitingAppointment.objects.create(
        schedule=schedule,
        specialist=schedule.specialist,
        pet=pet,
        owner=pet.owner,
        appointment_time=appt_time,
        service=service,
        reason=reason or f'{service} for {pet.name}'
    )

    # Update booking count
    schedule.appointments_booked += 1
    schedule.save()

    return {
        'success': True,
        'appointment_id': appointment.id,
        'pet_name': pet.name,
        'specialist_name': schedule.specialist.name,
        'date': str(schedule.date),
        'appointment_time': str(appointment.appointment_time),
        'service': service,
        'message': f'Appointment booked for {pet.name} with {schedule.specialist.name}'
    }


@tool(
    name='update_referral_status',
    description='Update the status of a referral',
    parameters={
        'type': 'object',
        'properties': {
            'referral_id': {
                'type': 'integer',
                'description': 'ID of the referral'
            },
            'status': {
                'type': 'string',
                'description': 'New status',
                'enum': ['draft', 'sent', 'received', 'scheduled', 'seen',
                         'report_pending', 'completed', 'cancelled', 'declined']
            },
            'notes': {
                'type': 'string',
                'description': 'Optional notes about the status change'
            }
        },
        'required': ['referral_id', 'status']
    },
    permission='staff',
    module='referrals'
)
def update_referral_status(
    referral_id: int,
    status: str,
    notes: str = None,
    user=None
) -> dict:
    """Update referral status and add optional note."""
    from django.utils import timezone
    from apps.referrals.models import Referral, ReferralNote

    try:
        referral = Referral.objects.get(pk=referral_id)
    except Referral.DoesNotExist:
        return {'success': False, 'message': f'Referral {referral_id} not found'}

    old_status = referral.status
    referral.status = status

    # Update timestamps based on status
    now = timezone.now()
    if status == 'sent' and not referral.sent_at:
        referral.sent_at = now
    elif status == 'seen' and not referral.seen_at:
        referral.seen_at = now
    elif status == 'completed' and not referral.completed_at:
        referral.completed_at = now

    referral.save()

    # Add note if provided
    if notes:
        ReferralNote.objects.create(
            referral=referral,
            note=notes,
            is_internal=True,
            author=user
        )

    return {
        'success': True,
        'referral_id': referral.id,
        'referral_number': referral.referral_number,
        'old_status': old_status,
        'new_status': status,
        'message': f'Referral status updated from {old_status} to {status}'
    }


@tool(
    name='record_specialist_report',
    description='Record specialist findings and recommendations on a referral',
    parameters={
        'type': 'object',
        'properties': {
            'referral_id': {
                'type': 'integer',
                'description': 'ID of the referral'
            },
            'findings': {
                'type': 'string',
                'description': 'Specialist findings'
            },
            'diagnosis': {
                'type': 'string',
                'description': 'Specialist diagnosis'
            },
            'recommendations': {
                'type': 'string',
                'description': 'Treatment recommendations'
            }
        },
        'required': ['referral_id']
    },
    permission='staff',
    module='referrals'
)
def record_specialist_report(
    referral_id: int,
    findings: str = None,
    diagnosis: str = None,
    recommendations: str = None,
    user=None
) -> dict:
    """Record specialist report on a referral."""
    from apps.referrals.models import Referral

    try:
        referral = Referral.objects.get(pk=referral_id)
    except Referral.DoesNotExist:
        return {'success': False, 'message': f'Referral {referral_id} not found'}

    if findings:
        referral.specialist_findings = findings
    if diagnosis:
        referral.specialist_diagnosis = diagnosis
    if recommendations:
        referral.specialist_recommendations = recommendations

    referral.save()

    return {
        'success': True,
        'referral_id': referral.id,
        'referral_number': referral.referral_number,
        'pet_name': referral.pet.name,
        'findings_recorded': bool(findings),
        'diagnosis_recorded': bool(diagnosis),
        'recommendations_recorded': bool(recommendations),
        'message': 'Specialist report recorded'
    }


@tool(
    name='get_referral_status',
    description='Get the current status and details of a referral',
    parameters={
        'type': 'object',
        'properties': {
            'referral_id': {
                'type': 'integer',
                'description': 'ID of the referral'
            }
        },
        'required': ['referral_id']
    },
    permission='staff',
    module='referrals'
)
def get_referral_status(referral_id: int) -> dict:
    """Get referral status and details."""
    from apps.referrals.models import Referral

    try:
        referral = Referral.objects.select_related(
            'pet', 'owner', 'specialist'
        ).get(pk=referral_id)
    except Referral.DoesNotExist:
        return {'success': False, 'message': f'Referral {referral_id} not found'}

    return {
        'success': True,
        'referral_id': referral.id,
        'referral_number': referral.referral_number,
        'direction': referral.direction,
        'pet_name': referral.pet.name,
        'owner_name': f'{referral.owner.first_name} {referral.owner.last_name}'.strip() or referral.owner.email,
        'specialist_name': referral.specialist.name if referral.specialist else None,
        'status': referral.status,
        'urgency': referral.urgency,
        'reason': referral.reason,
        'clinical_summary': referral.clinical_summary,
        'requested_services': referral.requested_services,
        'sent_at': str(referral.sent_at) if referral.sent_at else None,
        'appointment_date': str(referral.appointment_date) if referral.appointment_date else None,
        'seen_at': str(referral.seen_at) if referral.seen_at else None,
        'completed_at': str(referral.completed_at) if referral.completed_at else None,
        'specialist_findings': referral.specialist_findings,
        'specialist_diagnosis': referral.specialist_diagnosis,
        'specialist_recommendations': referral.specialist_recommendations,
        'follow_up_needed': referral.follow_up_needed,
        'outcome': referral.outcome,
        'created_at': str(referral.created_at)
    }


# ============================================================================
# Emergency Services Tools
# ============================================================================


@tool(
    name="triage_emergency",
    description="Assess emergency severity based on reported symptoms",
    parameters={
        "type": "object",
        "properties": {
            "symptoms": {
                "type": "string",
                "description": "Description of symptoms reported by pet owner"
            },
            "species": {
                "type": "string",
                "description": "Pet species (dog, cat, bird, etc.)"
            },
            "pet_age": {
                "type": "string",
                "description": "Pet age (optional)"
            },
            "symptom_duration": {
                "type": "string",
                "description": "How long symptoms have been present (optional)"
            }
        },
        "required": ["symptoms", "species"]
    }
)
def triage_emergency(
    symptoms: str,
    species: str,
    pet_age: str = None,
    symptom_duration: str = None
) -> dict:
    """Assess emergency severity based on symptoms."""
    from apps.emergency.models import EmergencySymptom

    symptoms_lower = symptoms.lower()

    # Get all active symptoms from database
    known_symptoms = EmergencySymptom.objects.filter(is_active=True)

    matched_severity = 'low'
    matched_symptoms = []
    first_aid = None
    recommendations = []

    for symptom in known_symptoms:
        # Check keyword match
        keywords_to_check = (
            [symptom.keyword.lower()] +
            [k.lower() for k in symptom.keywords_es] +
            [k.lower() for k in symptom.keywords_en]
        )

        for keyword in keywords_to_check:
            if keyword in symptoms_lower:
                matched_symptoms.append(symptom.keyword)

                # Update severity (critical > urgent > moderate > low)
                severity_order = ['low', 'moderate', 'urgent', 'critical']
                if severity_order.index(symptom.severity) > severity_order.index(matched_severity):
                    matched_severity = symptom.severity

                if symptom.first_aid_instructions and not first_aid:
                    first_aid = symptom.first_aid_instructions

                if symptom.follow_up_questions:
                    recommendations.extend(symptom.follow_up_questions)
                break

    # Default recommendations based on severity
    if not recommendations:
        if matched_severity == 'critical':
            recommendations = ['Seek immediate veterinary care', 'Keep pet calm and warm']
        elif matched_severity == 'urgent':
            recommendations = ['Schedule same-day appointment', 'Monitor closely']
        elif matched_severity == 'moderate':
            recommendations = ['Schedule appointment within 24-48 hours']
        else:
            recommendations = ['Monitor symptoms', 'Schedule regular appointment if symptoms persist']

    return {
        'severity': matched_severity,
        'requires_immediate_attention': matched_severity in ['critical', 'urgent'],
        'matched_symptoms': matched_symptoms,
        'first_aid': first_aid,
        'recommendations': recommendations[:5],
        'species': species,
        'pet_age': pet_age,
        'symptom_duration': symptom_duration
    }


@tool(
    name="get_oncall_status",
    description="Get current on-call veterinarian status",
    parameters={
        "type": "object",
        "properties": {}
    }
)
def get_oncall_status() -> dict:
    """Get current on-call veterinarian."""
    from django.utils import timezone
    from apps.emergency.models import OnCallSchedule

    now = timezone.now()
    current_time = now.time()

    # Find active on-call schedule for today
    schedules = OnCallSchedule.objects.filter(
        date=now.date(),
        is_active=True
    ).select_related('staff', 'staff__user')

    for schedule in schedules:
        # Check if current time is within schedule
        if schedule.start_time <= current_time or current_time <= schedule.end_time:
            staff = schedule.staff
            user = staff.user
            return {
                'is_on_call': True,
                'staff_name': user.get_full_name() or user.email,
                'staff_role': staff.get_role_display(),
                'contact_phone': schedule.contact_phone,
                'backup_phone': schedule.backup_phone or None,
                'schedule_start': str(schedule.start_time),
                'schedule_end': str(schedule.end_time),
            }

    return {
        'is_on_call': False,
        'message': 'No veterinarian currently on call',
        'recommendation': 'For emergencies, contact the nearest 24-hour animal hospital'
    }


@tool(
    name="get_emergency_referrals",
    description="Get nearby emergency veterinary hospitals",
    parameters={
        "type": "object",
        "properties": {
            "is_24_hours": {
                "type": "boolean",
                "description": "Filter for 24-hour facilities only"
            },
            "species": {
                "type": "string",
                "description": "Filter by species treated"
            }
        }
    }
)
def get_emergency_referrals(
    is_24_hours: bool = False,
    species: str = None
) -> dict:
    """Get emergency referral hospitals."""
    from apps.emergency.models import EmergencyReferral

    hospitals = EmergencyReferral.objects.filter(is_active=True)

    if is_24_hours:
        hospitals = hospitals.filter(is_24_hours=True)

    # Filter by species in Python to avoid JSONField contains lookup issues
    if species:
        hospitals = [h for h in hospitals if species in (h.species_treated or []) or 'all' in (h.species_treated or [])]
    else:
        hospitals = list(hospitals)

    return {
        'count': len(hospitals),
        'hospitals': [
            {
                'id': h.id,
                'name': h.name,
                'address': h.address,
                'phone': h.phone,
                'whatsapp': h.whatsapp or None,
                'is_24_hours': h.is_24_hours,
                'distance_km': h.distance_km,
                'services': h.services,
                'species_treated': h.species_treated,
            }
            for h in hospitals
        ]
    }


@tool(
    name="get_first_aid_instructions",
    description="Get first aid instructions for a condition",
    parameters={
        "type": "object",
        "properties": {
            "condition": {
                "type": "string",
                "description": "The emergency condition (e.g., 'choking', 'bleeding', 'poisoning')"
            },
            "species": {
                "type": "string",
                "description": "Pet species (optional)"
            }
        },
        "required": ["condition"]
    }
)
def get_first_aid_instructions(
    condition: str,
    species: str = None
) -> dict:
    """Get first aid instructions for a condition."""
    from apps.emergency.models import EmergencyFirstAid

    condition_lower = condition.lower()

    # Search for matching first aid guide
    guides = EmergencyFirstAid.objects.filter(
        is_active=True,
        condition__icontains=condition_lower
    )

    if not guides.exists():
        # Try title search
        guides = EmergencyFirstAid.objects.filter(
            is_active=True,
            title__icontains=condition_lower
        )

    if not guides.exists():
        return {
            'found': False,
            'message': f'No first aid instructions found for "{condition}"',
            'recommendation': 'Contact a veterinarian for guidance'
        }

    guide = guides.first()

    return {
        'found': True,
        'title': guide.title,
        'title_es': guide.title_es,
        'description': guide.description,
        'description_es': guide.description_es,
        'steps': guide.steps,
        'warnings': guide.warnings,
        'do_not': guide.do_not,
        'video_url': guide.video_url or None,
    }


@tool(
    name="escalate_to_oncall",
    description="Escalate emergency to on-call veterinarian",
    parameters={
        "type": "object",
        "properties": {
            "emergency_contact_id": {
                "type": "integer",
                "description": "ID of the emergency contact record"
            },
            "urgency": {
                "type": "string",
                "description": "Urgency level (critical, urgent, moderate)"
            },
            "callback_number": {
                "type": "string",
                "description": "Phone number for callback"
            }
        },
        "required": ["emergency_contact_id", "callback_number"]
    }
)
def escalate_to_oncall(
    emergency_contact_id: int,
    callback_number: str,
    urgency: str = 'urgent'
) -> dict:
    """Escalate emergency to on-call veterinarian."""
    from django.utils import timezone
    from apps.emergency.models import EmergencyContact, OnCallSchedule

    try:
        contact = EmergencyContact.objects.get(pk=emergency_contact_id)
    except EmergencyContact.DoesNotExist:
        return {'escalated': False, 'message': 'Emergency contact not found'}

    # Find on-call staff
    now = timezone.now()
    current_time = now.time()

    schedules = OnCallSchedule.objects.filter(
        date=now.date(),
        is_active=True
    ).select_related('staff', 'staff__user')

    on_call_staff = None
    for schedule in schedules:
        if schedule.start_time <= current_time or current_time <= schedule.end_time:
            on_call_staff = schedule.staff
            break

    if not on_call_staff:
        return {
            'escalated': False,
            'message': 'No on-call veterinarian available',
            'recommendation': 'Refer to 24-hour emergency hospital'
        }

    # Update emergency contact
    contact.status = 'escalated'
    contact.escalated_at = now
    contact.handled_by = on_call_staff
    contact.save()

    user = on_call_staff.user
    return {
        'escalated': True,
        'on_call_vet': user.get_full_name() or user.email,
        'contact_phone': schedule.contact_phone,
        'callback_number': callback_number,
        'urgency': urgency,
        'message': f'Escalated to {user.get_full_name() or user.email}. They will call back shortly.'
    }


@tool(
    name="create_emergency_contact",
    description="Create an emergency contact record",
    parameters={
        "type": "object",
        "properties": {
            "phone": {
                "type": "string",
                "description": "Contact phone number"
            },
            "channel": {
                "type": "string",
                "description": "Contact channel (web, whatsapp, phone, sms)"
            },
            "symptoms": {
                "type": "string",
                "description": "Reported symptoms"
            },
            "pet_species": {
                "type": "string",
                "description": "Pet species"
            },
            "owner_id": {
                "type": "integer",
                "description": "Owner user ID (optional)"
            },
            "pet_id": {
                "type": "integer",
                "description": "Pet ID (optional)"
            }
        },
        "required": ["phone", "channel", "symptoms", "pet_species"]
    }
)
def create_emergency_contact(
    phone: str,
    channel: str,
    symptoms: str,
    pet_species: str,
    owner_id: int = None,
    pet_id: int = None
) -> dict:
    """Create an emergency contact record."""
    from apps.emergency.models import EmergencyContact
    from apps.accounts.models import User
    from apps.pets.models import Pet

    owner = None
    pet = None

    if owner_id:
        try:
            owner = User.objects.get(pk=owner_id)
        except User.DoesNotExist:
            pass

    if pet_id:
        try:
            pet = Pet.objects.get(pk=pet_id)
        except Pet.DoesNotExist:
            pass

    contact = EmergencyContact.objects.create(
        owner=owner,
        pet=pet,
        phone=phone,
        channel=channel,
        reported_symptoms=symptoms,
        pet_species=pet_species,
        status='initiated'
    )

    return {
        'success': True,
        'emergency_contact_id': contact.id,
        'message': 'Emergency contact created'
    }


@tool(
    name="log_emergency_resolution",
    description="Log how an emergency was resolved",
    parameters={
        "type": "object",
        "properties": {
            "emergency_contact_id": {
                "type": "integer",
                "description": "ID of the emergency contact record"
            },
            "outcome": {
                "type": "string",
                "description": "Resolution outcome (seen_at_clinic, referred, advice_given, false_alarm)"
            },
            "notes": {
                "type": "string",
                "description": "Resolution notes"
            }
        },
        "required": ["emergency_contact_id", "outcome"]
    }
)
def log_emergency_resolution(
    emergency_contact_id: int,
    outcome: str,
    notes: str = ""
) -> dict:
    """Log emergency resolution."""
    from django.utils import timezone
    from apps.emergency.models import EmergencyContact

    try:
        contact = EmergencyContact.objects.get(pk=emergency_contact_id)
    except EmergencyContact.DoesNotExist:
        return {'success': False, 'message': 'Emergency contact not found'}

    contact.status = 'resolved'
    contact.outcome = outcome
    contact.resolution = notes
    contact.resolved_at = timezone.now()
    contact.save()

    return {
        'success': True,
        'emergency_contact_id': contact.id,
        'outcome': outcome,
        'message': 'Emergency resolution logged'
    }


# =============================================================================
# Omnichannel Communications Tools (S-006)
# =============================================================================


@tool(
    name="send_message",
    description="Send a message to a user through their preferred communication channel",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "ID of the user to send message to"
            },
            "message": {
                "type": "string",
                "description": "Message content to send"
            },
            "channel": {
                "type": "string",
                "enum": ["email", "sms", "whatsapp", "voice"],
                "description": "Communication channel to use"
            },
            "subject": {
                "type": "string",
                "description": "Message subject (for email)"
            }
        },
        "required": ["user_id", "message", "channel"]
    }
)
def send_message(
    user_id: int,
    message: str,
    channel: str,
    subject: str = ""
) -> dict:
    """Send a message through specified communication channel."""
    from apps.accounts.models import User
    from apps.communications.models import CommunicationChannel, Message

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'User not found'}

    # Find user's channel for this type
    try:
        user_channel = CommunicationChannel.objects.get(
            user=user,
            channel_type=channel,
            is_verified=True
        )
    except CommunicationChannel.DoesNotExist:
        return {
            'success': False,
            'message': f'No verified {channel} channel for user'
        }

    # Create message record
    msg = Message.objects.create(
        user=user,
        channel=channel,
        direction='outbound',
        recipient=user_channel.identifier,
        subject=subject,
        body=message,
        status='pending'
    )

    # In production, this would trigger actual sending via Twilio/SendGrid/etc.
    # For now, mark as sent
    from django.utils import timezone
    msg.status = 'sent'
    msg.sent_at = timezone.now()
    msg.save()

    return {
        'success': True,
        'message_id': msg.id,
        'channel': channel,
        'recipient': user_channel.identifier
    }


@tool(
    name="get_unread_messages",
    description="Get unread inbound messages from customers",
    parameters={
        "type": "object",
        "properties": {
            "channel": {
                "type": "string",
                "enum": ["email", "sms", "whatsapp", "voice", "all"],
                "description": "Filter by channel (or 'all')"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of messages to return"
            }
        },
        "required": []
    }
)
def get_unread_messages(
    channel: str = "all",
    limit: int = 20
) -> dict:
    """Get unread inbound messages."""
    from apps.communications.models import Message

    queryset = Message.objects.filter(
        direction='inbound',
        read_at__isnull=True
    )

    if channel != "all":
        queryset = queryset.filter(channel=channel)

    messages = queryset.order_by('-created_at')[:limit]

    return {
        'success': True,
        'count': messages.count(),
        'messages': [
            {
                'id': msg.id,
                'channel': msg.channel,
                'recipient': msg.recipient,
                'body': msg.body,
                'status': msg.status,
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
                'user_id': msg.user_id
            }
            for msg in messages
        ]
    }


@tool(
    name="schedule_reminder",
    description="Schedule a reminder notification for a user",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "ID of the user to remind"
            },
            "reminder_type": {
                "type": "string",
                "enum": ["appointment", "vaccination", "prescription", "followup"],
                "description": "Type of reminder"
            },
            "scheduled_for": {
                "type": "string",
                "description": "When to send (ISO 8601 format)"
            },
            "message": {
                "type": "string",
                "description": "Reminder message content"
            }
        },
        "required": ["user_id", "reminder_type", "scheduled_for"]
    }
)
def schedule_reminder(
    user_id: int,
    reminder_type: str,
    scheduled_for: str,
    message: str = ""
) -> dict:
    """Schedule a reminder for a user."""
    from datetime import datetime
    from django.utils import timezone
    from django.contrib.contenttypes.models import ContentType
    from apps.accounts.models import User
    from apps.communications.models import ReminderSchedule

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'User not found'}

    # Parse scheduled time
    try:
        if scheduled_for.endswith('Z'):
            scheduled_for = scheduled_for[:-1] + '+00:00'
        scheduled_time = datetime.fromisoformat(scheduled_for)
        if timezone.is_naive(scheduled_time):
            scheduled_time = timezone.make_aware(scheduled_time)
    except ValueError:
        return {'success': False, 'message': 'Invalid datetime format'}

    # Create reminder linked to user
    content_type = ContentType.objects.get_for_model(User)

    reminder = ReminderSchedule.objects.create(
        reminder_type=reminder_type,
        content_type=content_type,
        object_id=user.id,
        scheduled_for=scheduled_time,
        message=message
    )

    return {
        'success': True,
        'reminder_id': reminder.id,
        'reminder_type': reminder_type,
        'scheduled_for': scheduled_time.isoformat()
    }


@tool(
    name="check_message_status",
    description="Check the delivery status of a sent message",
    parameters={
        "type": "object",
        "properties": {
            "message_id": {
                "type": "integer",
                "description": "ID of the message to check"
            }
        },
        "required": ["message_id"]
    }
)
def check_message_status(message_id: int) -> dict:
    """Check message delivery status."""
    from apps.communications.models import Message

    try:
        message = Message.objects.get(pk=message_id)
    except Message.DoesNotExist:
        return {'success': False, 'message': 'Message not found'}

    return {
        'success': True,
        'message_id': message.id,
        'status': message.status,
        'channel': message.channel,
        'recipient': message.recipient,
        'sent_at': message.sent_at.isoformat() if message.sent_at else None,
        'delivered_at': message.delivered_at.isoformat() if message.delivered_at else None,
        'read_at': message.read_at.isoformat() if message.read_at else None,
        'external_id': message.external_id
    }


@tool(
    name="get_conversation_history",
    description="Get message history for a specific user",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "ID of the user"
            },
            "channel": {
                "type": "string",
                "enum": ["email", "sms", "whatsapp", "voice", "all"],
                "description": "Filter by channel"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of messages"
            }
        },
        "required": ["user_id"]
    }
)
def get_conversation_history(
    user_id: int,
    channel: str = "all",
    limit: int = 50
) -> dict:
    """Get conversation history for a user."""
    from apps.communications.models import Message

    queryset = Message.objects.filter(user_id=user_id)

    if channel != "all":
        queryset = queryset.filter(channel=channel)

    messages = queryset.order_by('-created_at')[:limit]

    return {
        'success': True,
        'user_id': user_id,
        'count': messages.count(),
        'messages': [
            {
                'id': msg.id,
                'channel': msg.channel,
                'direction': msg.direction,
                'recipient': msg.recipient,
                'subject': msg.subject,
                'body': msg.body,
                'status': msg.status,
                'created_at': msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
    }


# =============================================================================
# CRM Tools (S-007)
# =============================================================================


@tool(
    name="get_customer_profile",
    description="Get CRM profile for a customer including preferences, tags, and analytics",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "ID of the user/customer"
            }
        },
        "required": ["user_id"]
    }
)
def get_customer_profile(user_id: int) -> dict:
    """Get customer CRM profile."""
    from apps.accounts.models import User
    from apps.crm.models import OwnerProfile

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'User not found'}

    try:
        profile = OwnerProfile.objects.get(user=user)
    except OwnerProfile.DoesNotExist:
        return {'success': False, 'message': 'No CRM profile for user'}

    return {
        'success': True,
        'user_id': user.id,
        'name': user.get_full_name(),
        'email': user.email,
        'preferred_language': profile.preferred_language,
        'preferred_contact_method': profile.preferred_contact_method,
        'marketing_preferences': profile.marketing_preferences,
        'notes': profile.notes,
        'tags': [tag.name for tag in profile.tags.all()],
        'first_visit': profile.first_visit_date.isoformat() if profile.first_visit_date else None,
        'last_visit': profile.last_visit_date.isoformat() if profile.last_visit_date else None,
        'total_visits': profile.total_visits,
        'total_spent': str(profile.total_spent),
        'lifetime_value': str(profile.lifetime_value),
    }


@tool(
    name="add_customer_note",
    description="Add an internal note to a customer's CRM profile",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "ID of the customer"
            },
            "note": {
                "type": "string",
                "description": "Note content"
            },
            "author_id": {
                "type": "integer",
                "description": "ID of the staff member adding the note"
            },
            "is_pinned": {
                "type": "boolean",
                "description": "Whether to pin this note"
            }
        },
        "required": ["user_id", "note"]
    }
)
def add_customer_note(
    user_id: int,
    note: str,
    author_id: int = None,
    is_pinned: bool = False
) -> dict:
    """Add a note to customer profile."""
    from apps.accounts.models import User
    from apps.crm.models import OwnerProfile, CustomerNote

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'User not found'}

    try:
        profile = OwnerProfile.objects.get(user=user)
    except OwnerProfile.DoesNotExist:
        profile = OwnerProfile.objects.create(user=user)

    author = None
    if author_id:
        try:
            author = User.objects.get(pk=author_id)
        except User.DoesNotExist:
            pass

    customer_note = CustomerNote.objects.create(
        owner_profile=profile,
        author=author,
        content=note,
        is_pinned=is_pinned,
    )

    return {
        'success': True,
        'note_id': customer_note.id,
        'message': 'Note added successfully'
    }


@tool(
    name="log_interaction",
    description="Log a customer interaction (call, email, chat, visit)",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "ID of the customer"
            },
            "interaction_type": {
                "type": "string",
                "enum": ["call", "email", "chat", "visit", "sms", "whatsapp"],
                "description": "Type of interaction"
            },
            "channel": {
                "type": "string",
                "description": "Communication channel used"
            },
            "direction": {
                "type": "string",
                "enum": ["inbound", "outbound"],
                "description": "Direction of interaction"
            },
            "subject": {
                "type": "string",
                "description": "Subject or reason"
            },
            "notes": {
                "type": "string",
                "description": "Interaction notes"
            }
        },
        "required": ["user_id", "interaction_type", "channel", "direction"]
    }
)
def log_interaction(
    user_id: int,
    interaction_type: str,
    channel: str,
    direction: str,
    subject: str = "",
    notes: str = ""
) -> dict:
    """Log a customer interaction."""
    from apps.accounts.models import User
    from apps.crm.models import OwnerProfile, Interaction

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'User not found'}

    try:
        profile = OwnerProfile.objects.get(user=user)
    except OwnerProfile.DoesNotExist:
        profile = OwnerProfile.objects.create(user=user)

    interaction = Interaction.objects.create(
        owner_profile=profile,
        interaction_type=interaction_type,
        channel=channel,
        direction=direction,
        subject=subject,
        notes=notes,
    )

    return {
        'success': True,
        'interaction_id': interaction.id,
        'message': 'Interaction logged'
    }


@tool(
    name="get_customer_history",
    description="Get interaction history for a customer",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "ID of the customer"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of interactions"
            }
        },
        "required": ["user_id"]
    }
)
def get_customer_history(user_id: int, limit: int = 20) -> dict:
    """Get customer interaction history."""
    from apps.accounts.models import User
    from apps.crm.models import OwnerProfile, Interaction

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'User not found'}

    try:
        profile = OwnerProfile.objects.get(user=user)
    except OwnerProfile.DoesNotExist:
        return {'success': True, 'interaction_count': 0, 'interactions': []}

    interactions = Interaction.objects.filter(
        owner_profile=profile
    ).order_by('-created_at')[:limit]

    return {
        'success': True,
        'user_id': user_id,
        'interaction_count': interactions.count(),
        'interactions': [
            {
                'id': i.id,
                'type': i.interaction_type,
                'channel': i.channel,
                'direction': i.direction,
                'subject': i.subject,
                'notes': i.notes,
                'created_at': i.created_at.isoformat(),
            }
            for i in interactions
        ]
    }


@tool(
    name="search_customers",
    description="Search customers by name, email, or phone",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results"
            }
        },
        "required": ["query"]
    }
)
def search_customers(query: str, limit: int = 20) -> dict:
    """Search customers."""
    from django.db.models import Q
    from apps.accounts.models import User
    from apps.crm.models import OwnerProfile

    users = User.objects.filter(
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(phone_number__icontains=query)
    )[:limit]

    return {
        'success': True,
        'count': users.count(),
        'customers': [
            {
                'id': u.id,
                'email': u.email,
                'name': u.get_full_name(),
                'phone': getattr(u, 'phone_number', ''),
                'has_crm_profile': OwnerProfile.objects.filter(user=u).exists(),
            }
            for u in users
        ]
    }


@tool(
    name="tag_customer",
    description="Add a tag to a customer profile",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "ID of the customer"
            },
            "tag_name": {
                "type": "string",
                "description": "Name of the tag to add"
            }
        },
        "required": ["user_id", "tag_name"]
    }
)
def tag_customer(user_id: int, tag_name: str) -> dict:
    """Add a tag to customer."""
    from apps.accounts.models import User
    from apps.crm.models import OwnerProfile, CustomerTag

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'User not found'}

    try:
        profile = OwnerProfile.objects.get(user=user)
    except OwnerProfile.DoesNotExist:
        profile = OwnerProfile.objects.create(user=user)

    try:
        tag = CustomerTag.objects.get(name=tag_name)
    except CustomerTag.DoesNotExist:
        return {'success': False, 'message': f'Tag "{tag_name}" not found'}

    profile.tags.add(tag)

    return {
        'success': True,
        'message': f'Tag "{tag_name}" added to customer'
    }


# =============================================================================
# Competitive Intelligence Tools (S-009)
# =============================================================================


@tool(
    name="get_competitors",
    description="Get list of competing veterinary clinics",
    parameters={
        "type": "object",
        "properties": {
            "active_only": {
                "type": "boolean",
                "description": "Only return active competitors"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number to return"
            }
        },
        "required": []
    }
)
def get_competitors(active_only: bool = True, limit: int = 20) -> dict:
    """Get list of competitors."""
    from apps.competitive.models import Competitor

    queryset = Competitor.objects.all()
    if active_only:
        queryset = queryset.filter(is_active=True)

    competitors = queryset.order_by('distance_km', 'name')[:limit]

    return {
        'success': True,
        'count': competitors.count(),
        'competitors': [
            {
                'id': c.id,
                'name': c.name,
                'address': c.address,
                'phone': c.phone,
                'distance_km': str(c.distance_km) if c.distance_km else None,
                'services': c.services_offered,
            }
            for c in competitors
        ]
    }


@tool(
    name="get_competitor_prices",
    description="Get competitor prices for a specific service",
    parameters={
        "type": "object",
        "properties": {
            "service_name": {
                "type": "string",
                "description": "Name of the service to compare"
            },
            "competitor_id": {
                "type": "integer",
                "description": "Optional: specific competitor ID"
            }
        },
        "required": ["service_name"]
    }
)
def get_competitor_prices(
    service_name: str,
    competitor_id: int = None
) -> dict:
    """Get competitor prices for a service."""
    from apps.competitive.models import CompetitorService

    queryset = CompetitorService.objects.filter(
        name__icontains=service_name,
        competitor__is_active=True
    )

    if competitor_id:
        queryset = queryset.filter(competitor_id=competitor_id)

    services = queryset.select_related('competitor')

    return {
        'success': True,
        'service_name': service_name,
        'prices': [
            {
                'competitor': s.competitor.name,
                'competitor_id': s.competitor.id,
                'price': str(s.price),
                'currency': s.currency,
                'our_price': str(s.our_price) if s.our_price else None,
                'difference': str(s.price_difference) if s.price_difference else None,
            }
            for s in services
        ]
    }


@tool(
    name="add_competitor",
    description="Add a new competitor to track",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Competitor name"
            },
            "address": {
                "type": "string",
                "description": "Address"
            },
            "phone": {
                "type": "string",
                "description": "Phone number"
            },
            "website": {
                "type": "string",
                "description": "Website URL"
            }
        },
        "required": ["name"]
    }
)
def add_competitor(
    name: str,
    address: str = "",
    phone: str = "",
    website: str = ""
) -> dict:
    """Add a new competitor."""
    from apps.competitive.models import Competitor

    competitor = Competitor.objects.create(
        name=name,
        address=address,
        phone=phone,
        website=website,
        is_active=True,
    )

    return {
        'success': True,
        'competitor_id': competitor.id,
        'message': f'Competitor "{name}" added'
    }


@tool(
    name="update_competitor_price",
    description="Update a competitor's service price",
    parameters={
        "type": "object",
        "properties": {
            "competitor_id": {
                "type": "integer",
                "description": "Competitor ID"
            },
            "service_name": {
                "type": "string",
                "description": "Service name"
            },
            "new_price": {
                "type": "number",
                "description": "New price"
            }
        },
        "required": ["competitor_id", "service_name", "new_price"]
    }
)
def update_competitor_price(
    competitor_id: int,
    service_name: str,
    new_price: float
) -> dict:
    """Update competitor service price."""
    from decimal import Decimal
    from apps.competitive.models import Competitor, CompetitorService, PriceHistory

    try:
        competitor = Competitor.objects.get(pk=competitor_id)
    except Competitor.DoesNotExist:
        return {'success': False, 'message': 'Competitor not found'}

    try:
        service = CompetitorService.objects.get(
            competitor=competitor,
            name=service_name
        )
        # Record history
        PriceHistory.objects.create(
            service=service,
            price=service.price,
        )
        # Update price
        service.previous_price = service.price
        service.price = Decimal(str(new_price))
        service.save()
    except CompetitorService.DoesNotExist:
        # Create new service
        service = CompetitorService.objects.create(
            competitor=competitor,
            name=service_name,
            price=Decimal(str(new_price)),
        )

    return {
        'success': True,
        'service_id': service.id,
        'message': f'Price updated to {new_price}'
    }


@tool(
    name="get_market_position",
    description="Get market position analysis based on reviews and ratings",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_market_position() -> dict:
    """Get market position analysis."""
    from django.db.models import Avg, Count
    from apps.competitive.models import Competitor, CompetitorReview

    # Get average ratings by competitor
    competitors = Competitor.objects.filter(is_active=True).annotate(
        avg_rating=Avg('reviews__rating'),
        total_reviews=Count('reviews')
    ).order_by('-avg_rating')

    return {
        'success': True,
        'market_analysis': [
            {
                'name': c.name,
                'avg_rating': round(float(c.avg_rating), 1) if c.avg_rating else None,
                'total_reviews': c.total_reviews,
                'distance_km': str(c.distance_km) if c.distance_km else None,
            }
            for c in competitors
        ]
    }


# =============================================================================
# Reviews & Testimonials Tools
# =============================================================================

@tool(
    name="get_reviews",
    description="Get customer reviews optionally filtered by status or rating",
    parameters={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter by status (pending, approved, featured, rejected)",
                "enum": ["pending", "approved", "featured", "rejected"]
            },
            "min_rating": {
                "type": "integer",
                "description": "Minimum rating filter (1-5)"
            },
            "platform": {
                "type": "string",
                "description": "Filter by platform",
                "enum": ["internal", "google", "facebook", "yelp"]
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of reviews to return"
            }
        },
        "required": []
    }
)
def get_reviews(
    status: str = None,
    min_rating: int = None,
    platform: str = None,
    limit: int = 20
) -> dict:
    """Get customer reviews with optional filters."""
    from apps.reviews.models import Review

    reviews = Review.objects.all()

    if status:
        reviews = reviews.filter(status=status)
    if min_rating:
        reviews = reviews.filter(rating__gte=min_rating)
    if platform:
        reviews = reviews.filter(platform=platform)

    reviews = reviews[:limit]

    return {
        'success': True,
        'count': reviews.count(),
        'reviews': [
            {
                'id': r.id,
                'author': r.author,
                'rating': r.rating,
                'title': r.title,
                'content': r.content,
                'platform': r.platform,
                'status': r.status,
                'display_on_homepage': r.display_on_homepage,
                'created_at': r.created_at.isoformat(),
                'response': r.response if r.response else None,
            }
            for r in reviews
        ]
    }


@tool(
    name="submit_review",
    description="Submit a new review for the clinic",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "User ID submitting the review"
            },
            "rating": {
                "type": "integer",
                "description": "Rating from 1-5 stars"
            },
            "content": {
                "type": "string",
                "description": "Review content"
            },
            "title": {
                "type": "string",
                "description": "Review title"
            },
            "pet_id": {
                "type": "integer",
                "description": "Pet ID associated with review"
            }
        },
        "required": ["rating", "content"]
    }
)
def submit_review(
    rating: int,
    content: str,
    user_id: int = None,
    title: str = '',
    pet_id: int = None
) -> dict:
    """Submit a new review."""
    from apps.reviews.models import Review
    from apps.accounts.models import User
    from apps.pets.models import Pet

    user = None
    if user_id:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            pass

    pet = None
    if pet_id:
        try:
            pet = Pet.objects.get(pk=pet_id)
        except Pet.DoesNotExist:
            pass

    review = Review.objects.create(
        user=user,
        pet=pet,
        rating=rating,
        title=title,
        content=content,
        status='pending',
        platform='internal',
    )

    return {
        'success': True,
        'review_id': review.id,
        'message': 'Review submitted successfully. It will be visible after approval.'
    }


@tool(
    name="request_review",
    description="Send a review request to a customer after their visit",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "Customer user ID"
            },
            "pet_id": {
                "type": "integer",
                "description": "Pet ID"
            },
            "appointment_id": {
                "type": "integer",
                "description": "Related appointment ID"
            },
            "service_description": {
                "type": "string",
                "description": "Description of service provided"
            }
        },
        "required": ["user_id"]
    }
)
def request_review(
    user_id: int,
    pet_id: int = None,
    appointment_id: int = None,
    service_description: str = ''
) -> dict:
    """Send a review request to customer."""
    from apps.reviews.models import ReviewRequest
    from apps.accounts.models import User
    from apps.pets.models import Pet
    from apps.appointments.models import Appointment

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'User not found'}

    pet = None
    if pet_id:
        try:
            pet = Pet.objects.get(pk=pet_id)
        except Pet.DoesNotExist:
            pass

    appointment = None
    if appointment_id:
        try:
            appointment = Appointment.objects.get(pk=appointment_id)
        except Appointment.DoesNotExist:
            pass

    request = ReviewRequest.objects.create(
        user=user,
        pet=pet,
        appointment=appointment,
        service_description=service_description,
    )

    return {
        'success': True,
        'request_id': request.id,
        'token': request.token,
        'message': f'Review request created for {user.email}'
    }


@tool(
    name="get_testimonials",
    description="Get testimonials for marketing display",
    parameters={
        "type": "object",
        "properties": {
            "homepage_only": {
                "type": "boolean",
                "description": "Only return testimonials marked for homepage display"
            },
            "active_only": {
                "type": "boolean",
                "description": "Only return active testimonials"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of testimonials"
            }
        },
        "required": []
    }
)
def get_testimonials(
    homepage_only: bool = False,
    active_only: bool = True,
    limit: int = 10
) -> dict:
    """Get testimonials for display."""
    from apps.reviews.models import Testimonial

    testimonials = Testimonial.objects.all()

    if active_only:
        testimonials = testimonials.filter(is_active=True)
    if homepage_only:
        testimonials = testimonials.filter(show_on_homepage=True)

    testimonials = testimonials.order_by('display_order', '-created_at')[:limit]

    return {
        'success': True,
        'count': testimonials.count(),
        'testimonials': [
            {
                'id': t.id,
                'author_name': t.author_name,
                'author_title': t.author_title,
                'quote': t.quote,
                'short_quote': t.short_quote,
                'show_on_homepage': t.show_on_homepage,
                'show_on_services': t.show_on_services,
                'tags': t.tags,
            }
            for t in testimonials
        ]
    }


# =============================================================================
# Loyalty & Rewards Tools
# =============================================================================

@tool(
    name="get_loyalty_status",
    description="Get customer's loyalty program status including points and tier",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "User ID to check"
            }
        },
        "required": ["user_id"]
    }
)
def get_loyalty_status(user_id: int) -> dict:
    """Get loyalty program status for user."""
    from apps.loyalty.models import LoyaltyAccount

    try:
        account = LoyaltyAccount.objects.select_related('tier', 'program').get(
            user_id=user_id
        )
    except LoyaltyAccount.DoesNotExist:
        return {'success': False, 'message': 'No loyalty account found'}

    return {
        'success': True,
        'points_balance': account.points_balance,
        'lifetime_points': account.lifetime_points,
        'tier': account.tier.name if account.tier else None,
        'tier_discount': float(account.tier.discount_percent) if account.tier else 0,
        'program': account.program.name,
        'is_active': account.is_active,
    }


@tool(
    name="earn_points",
    description="Award points to a customer",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "User ID to award points"
            },
            "points": {
                "type": "integer",
                "description": "Number of points to award"
            },
            "description": {
                "type": "string",
                "description": "Description of why points were earned"
            },
            "transaction_type": {
                "type": "string",
                "description": "Type of transaction",
                "enum": ["earn", "bonus", "referral", "adjustment"]
            }
        },
        "required": ["user_id", "points", "description"]
    }
)
def earn_points(
    user_id: int,
    points: int,
    description: str,
    transaction_type: str = 'earn'
) -> dict:
    """Award points to customer."""
    from apps.loyalty.models import LoyaltyAccount, PointTransaction

    try:
        account = LoyaltyAccount.objects.get(user_id=user_id)
    except LoyaltyAccount.DoesNotExist:
        return {'success': False, 'message': 'No loyalty account found'}

    account.points_balance += points
    account.lifetime_points += points
    account.save()

    PointTransaction.objects.create(
        account=account,
        transaction_type=transaction_type,
        points=points,
        balance_after=account.points_balance,
        description=description,
    )

    account.update_tier()

    return {
        'success': True,
        'points_awarded': points,
        'new_balance': account.points_balance,
        'tier': account.tier.name if account.tier else None,
    }


@tool(
    name="redeem_reward",
    description="Redeem a loyalty reward for a customer",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "User ID redeeming"
            },
            "reward_id": {
                "type": "integer",
                "description": "Reward ID to redeem"
            }
        },
        "required": ["user_id", "reward_id"]
    }
)
def redeem_reward(user_id: int, reward_id: int) -> dict:
    """Redeem a loyalty reward."""
    from apps.loyalty.models import (
        LoyaltyAccount, LoyaltyReward, RewardRedemption, PointTransaction
    )

    try:
        account = LoyaltyAccount.objects.get(user_id=user_id)
    except LoyaltyAccount.DoesNotExist:
        return {'success': False, 'message': 'No loyalty account found'}

    try:
        reward = LoyaltyReward.objects.get(pk=reward_id, is_active=True)
    except LoyaltyReward.DoesNotExist:
        return {'success': False, 'message': 'Reward not found or inactive'}

    if account.points_balance < reward.points_cost:
        return {
            'success': False,
            'message': f'Insufficient points. Need {reward.points_cost}, have {account.points_balance}'
        }

    if reward.min_tier and account.tier:
        if account.tier.min_points < reward.min_tier.min_points:
            return {
                'success': False,
                'message': f'Tier {reward.min_tier.name} required'
            }

    account.points_balance -= reward.points_cost
    account.points_redeemed += reward.points_cost
    account.save()

    redemption = RewardRedemption.objects.create(
        account=account,
        reward=reward,
        points_spent=reward.points_cost,
        status='pending',
    )

    PointTransaction.objects.create(
        account=account,
        transaction_type='redeem',
        points=-reward.points_cost,
        balance_after=account.points_balance,
        description=f'Redeemed: {reward.name}',
    )

    reward.quantity_redeemed += 1
    reward.save()

    return {
        'success': True,
        'redemption_code': redemption.code,
        'reward_name': reward.name,
        'points_spent': reward.points_cost,
        'new_balance': account.points_balance,
    }


@tool(
    name="get_available_rewards",
    description="Get list of available rewards for a customer",
    parameters={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "integer",
                "description": "User ID to check rewards for"
            }
        },
        "required": ["user_id"]
    }
)
def get_available_rewards(user_id: int) -> dict:
    """Get available rewards for customer."""
    from django.db import models
    from django.utils import timezone
    from apps.loyalty.models import LoyaltyAccount, LoyaltyReward

    try:
        account = LoyaltyAccount.objects.get(user_id=user_id)
    except LoyaltyAccount.DoesNotExist:
        return {'success': False, 'message': 'No loyalty account found'}

    now = timezone.now()
    rewards = LoyaltyReward.objects.filter(
        program=account.program,
        is_active=True,
    ).filter(
        models.Q(valid_from__isnull=True) | models.Q(valid_from__lte=now)
    ).filter(
        models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=now)
    )

    return {
        'success': True,
        'points_balance': account.points_balance,
        'rewards': [
            {
                'id': r.id,
                'name': r.name,
                'description': r.description,
                'reward_type': r.reward_type,
                'points_cost': r.points_cost,
                'can_afford': account.points_balance >= r.points_cost,
                'is_featured': r.is_featured,
            }
            for r in rewards
        ]
    }


@tool(
    name="create_friend_referral",
    description="Create a referral for a customer to invite friends and earn rewards",
    parameters={
        "type": "object",
        "properties": {
            "referrer_id": {
                "type": "integer",
                "description": "User ID of person making referral"
            },
            "referred_email": {
                "type": "string",
                "description": "Email of person being referred"
            }
        },
        "required": ["referrer_id", "referred_email"]
    }
)
def create_friend_referral(referrer_id: int, referred_email: str) -> dict:
    """Create a friend referral for loyalty program."""
    from apps.loyalty.models import Referral
    from apps.accounts.models import User

    try:
        referrer = User.objects.get(pk=referrer_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'User not found'}

    if Referral.objects.filter(
        referrer=referrer,
        referred_email=referred_email
    ).exists():
        return {'success': False, 'message': 'Referral already exists'}

    referral = Referral.objects.create(
        referrer=referrer,
        referred_email=referred_email,
    )

    return {
        'success': True,
        'referral_code': referral.code,
        'message': f'Referral created for {referred_email}'
    }


# =============================================================================
# SEO & Content Marketing Tools
# =============================================================================

@tool(
    name="get_blog_posts",
    description="Get blog posts with optional filters",
    parameters={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter by status",
                "enum": ["draft", "review", "scheduled", "published", "archived"]
            },
            "category_slug": {
                "type": "string",
                "description": "Filter by category slug"
            },
            "is_featured": {
                "type": "boolean",
                "description": "Only featured posts"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum posts to return"
            }
        },
        "required": []
    }
)
def get_blog_posts(
    status: str = None,
    category_slug: str = None,
    is_featured: bool = None,
    limit: int = 20
) -> dict:
    """Get blog posts."""
    from apps.seo.models import BlogPost

    posts = BlogPost.objects.all()

    if status:
        posts = posts.filter(status=status)
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    if is_featured is not None:
        posts = posts.filter(is_featured=is_featured)

    posts = posts[:limit]

    return {
        'success': True,
        'count': posts.count(),
        'posts': [
            {
                'id': p.id,
                'title': p.title,
                'slug': p.slug,
                'excerpt': p.excerpt,
                'status': p.status,
                'is_featured': p.is_featured,
                'category': p.category.name if p.category else None,
                'published_at': p.published_at.isoformat() if p.published_at else None,
                'view_count': p.view_count,
            }
            for p in posts
        ]
    }


@tool(
    name="create_blog_post",
    description="Create a new blog post",
    parameters={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Post title"
            },
            "content": {
                "type": "string",
                "description": "Post content"
            },
            "author_id": {
                "type": "integer",
                "description": "Author user ID"
            },
            "excerpt": {
                "type": "string",
                "description": "Short excerpt"
            },
            "category_id": {
                "type": "integer",
                "description": "Category ID"
            },
            "status": {
                "type": "string",
                "description": "Post status",
                "enum": ["draft", "review", "scheduled", "published"]
            }
        },
        "required": ["title", "content"]
    }
)
def create_blog_post(
    title: str,
    content: str,
    author_id: int = None,
    excerpt: str = '',
    category_id: int = None,
    status: str = 'draft'
) -> dict:
    """Create a blog post."""
    from apps.seo.models import BlogPost, BlogCategory
    from apps.accounts.models import User

    author = None
    if author_id:
        try:
            author = User.objects.get(pk=author_id)
        except User.DoesNotExist:
            pass

    category = None
    if category_id:
        try:
            category = BlogCategory.objects.get(pk=category_id)
        except BlogCategory.DoesNotExist:
            pass

    post = BlogPost.objects.create(
        title=title,
        content=content,
        author=author,
        excerpt=excerpt,
        category=category,
        status=status,
    )

    return {
        'success': True,
        'post_id': post.id,
        'slug': post.slug,
        'message': f'Blog post "{title}" created as {status}'
    }


@tool(
    name="get_seo_metadata",
    description="Get SEO metadata for a specific path",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "URL path to get metadata for"
            }
        },
        "required": ["path"]
    }
)
def get_seo_metadata(path: str) -> dict:
    """Get SEO metadata for path."""
    from apps.seo.models import SEOMetadata

    try:
        meta = SEOMetadata.objects.get(path=path, is_active=True)
    except SEOMetadata.DoesNotExist:
        return {'success': False, 'message': 'No SEO metadata found for path'}

    return {
        'success': True,
        'path': meta.path,
        'title': meta.title,
        'description': meta.description,
        'keywords': meta.keywords,
        'og_title': meta.og_title,
        'og_description': meta.og_description,
        'robots': meta.robots,
    }


@tool(
    name="update_seo_metadata",
    description="Update or create SEO metadata for a path",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "URL path"
            },
            "title": {
                "type": "string",
                "description": "Meta title (max 70 chars)"
            },
            "description": {
                "type": "string",
                "description": "Meta description (max 160 chars)"
            },
            "keywords": {
                "type": "string",
                "description": "Meta keywords"
            }
        },
        "required": ["path", "title", "description"]
    }
)
def update_seo_metadata(
    path: str,
    title: str,
    description: str,
    keywords: str = ''
) -> dict:
    """Update SEO metadata."""
    from apps.seo.models import SEOMetadata

    meta, created = SEOMetadata.objects.update_or_create(
        path=path,
        defaults={
            'title': title[:70],
            'description': description[:160],
            'keywords': keywords,
        }
    )

    return {
        'success': True,
        'created': created,
        'path': meta.path,
        'message': f'SEO metadata {"created" if created else "updated"} for {path}'
    }


@tool(
    name="suggest_content",
    description="Get content suggestions based on existing content and trends",
    parameters={
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Topic area for suggestions"
            },
            "content_type": {
                "type": "string",
                "description": "Type of content",
                "enum": ["blog", "social", "email", "landing"]
            }
        },
        "required": []
    }
)
def suggest_content(
    topic: str = None,
    content_type: str = 'blog'
) -> dict:
    """Suggest content topics."""
    suggestions = [
        {
            'topic': 'Seasonal Pet Care Tips',
            'description': 'Tips for pet care during current season',
            'keywords': ['pet care', 'seasonal', 'health tips'],
        },
        {
            'topic': 'Common Pet Health Issues',
            'description': 'Educational content about pet health',
            'keywords': ['pet health', 'veterinary', 'symptoms'],
        },
        {
            'topic': 'Vaccination Schedules',
            'description': 'Guide to vaccination timing',
            'keywords': ['vaccines', 'puppy', 'kitten', 'schedule'],
        },
        {
            'topic': 'Traveling with Pets',
            'description': 'Tips for traveling with pets',
            'keywords': ['travel', 'pets', 'health certificate'],
        },
    ]

    if topic:
        suggestions = [s for s in suggestions if topic.lower() in s['topic'].lower()]

    return {
        'success': True,
        'content_type': content_type,
        'suggestions': suggestions,
    }


# =============================================================================
# Email Marketing Tools
# =============================================================================

@tool(
    name="subscribe_newsletter",
    description="Subscribe an email to the newsletter",
    parameters={
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "Email address to subscribe"
            },
            "source": {
                "type": "string",
                "description": "Where the subscription came from"
            },
            "user_id": {
                "type": "integer",
                "description": "Optional user ID to link"
            }
        },
        "required": ["email"]
    }
)
def subscribe_newsletter(
    email: str,
    source: str = 'website',
    user_id: int = None
) -> dict:
    """Subscribe email to newsletter."""
    from apps.email_marketing.models import NewsletterSubscription
    from apps.accounts.models import User

    if NewsletterSubscription.objects.filter(email=email).exists():
        existing = NewsletterSubscription.objects.get(email=email)
        if existing.status == 'active':
            return {'success': False, 'message': 'Email already subscribed'}
        if existing.status == 'unsubscribed':
            existing.status = 'pending'
            existing.save()
            return {
                'success': True,
                'subscription_id': existing.id,
                'message': 'Resubscribed. Please confirm your email.'
            }

    user = None
    if user_id:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            pass

    sub = NewsletterSubscription.objects.create(
        email=email,
        user=user,
        source=source,
    )

    return {
        'success': True,
        'subscription_id': sub.id,
        'confirmation_token': sub.confirmation_token,
        'message': 'Subscribed! Please check your email to confirm.'
    }


@tool(
    name="get_email_campaigns",
    description="Get email campaigns with optional filters",
    parameters={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter by status",
                "enum": ["draft", "scheduled", "sending", "sent", "cancelled"]
            },
            "limit": {
                "type": "integer",
                "description": "Maximum campaigns to return"
            }
        },
        "required": []
    }
)
def get_email_campaigns(
    status: str = None,
    limit: int = 20
) -> dict:
    """Get email campaigns."""
    from apps.email_marketing.models import EmailCampaign

    campaigns = EmailCampaign.objects.all()

    if status:
        campaigns = campaigns.filter(status=status)

    campaigns = campaigns[:limit]

    return {
        'success': True,
        'count': campaigns.count(),
        'campaigns': [
            {
                'id': c.id,
                'name': c.name,
                'subject': c.subject,
                'status': c.status,
                'total_sent': c.total_sent,
                'total_opened': c.total_opened,
                'open_rate': round(c.open_rate, 1),
                'click_rate': round(c.click_rate, 1),
                'sent_at': c.sent_at.isoformat() if c.sent_at else None,
            }
            for c in campaigns
        ]
    }


@tool(
    name="create_email_campaign",
    description="Create a new email campaign",
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Campaign name"
            },
            "subject": {
                "type": "string",
                "description": "Email subject"
            },
            "html_content": {
                "type": "string",
                "description": "HTML content"
            },
            "from_name": {
                "type": "string",
                "description": "From name"
            },
            "from_email": {
                "type": "string",
                "description": "From email"
            },
            "segment_id": {
                "type": "integer",
                "description": "Target segment ID"
            }
        },
        "required": ["name", "subject", "html_content", "from_name", "from_email"]
    }
)
def create_email_campaign(
    name: str,
    subject: str,
    html_content: str,
    from_name: str,
    from_email: str,
    segment_id: int = None
) -> dict:
    """Create an email campaign."""
    from apps.email_marketing.models import EmailCampaign, EmailSegment

    segment = None
    if segment_id:
        try:
            segment = EmailSegment.objects.get(pk=segment_id)
        except EmailSegment.DoesNotExist:
            pass

    campaign = EmailCampaign.objects.create(
        name=name,
        subject=subject,
        html_content=html_content,
        from_name=from_name,
        from_email=from_email,
        segment=segment,
    )

    return {
        'success': True,
        'campaign_id': campaign.id,
        'message': f'Campaign "{name}" created as draft'
    }


@tool(
    name="get_campaign_stats",
    description="Get statistics for an email campaign",
    parameters={
        "type": "object",
        "properties": {
            "campaign_id": {
                "type": "integer",
                "description": "Campaign ID"
            }
        },
        "required": ["campaign_id"]
    }
)
def get_campaign_stats(campaign_id: int) -> dict:
    """Get campaign statistics."""
    from apps.email_marketing.models import EmailCampaign

    try:
        campaign = EmailCampaign.objects.get(pk=campaign_id)
    except EmailCampaign.DoesNotExist:
        return {'success': False, 'message': 'Campaign not found'}

    return {
        'success': True,
        'campaign_id': campaign.id,
        'name': campaign.name,
        'status': campaign.status,
        'stats': {
            'total_recipients': campaign.total_recipients,
            'total_sent': campaign.total_sent,
            'total_delivered': campaign.total_delivered,
            'total_opened': campaign.total_opened,
            'total_clicked': campaign.total_clicked,
            'total_bounced': campaign.total_bounced,
            'total_unsubscribed': campaign.total_unsubscribed,
            'open_rate': round(campaign.open_rate, 1),
            'click_rate': round(campaign.click_rate, 1),
        }
    }


# =============================================================================
# Practice Management Tools
# =============================================================================

@tool(
    name="get_staff_schedule",
    description="Get staff schedule for a specific date",
    parameters={
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date in YYYY-MM-DD format"
            },
            "staff_id": {
                "type": "integer",
                "description": "Optional staff ID to filter by"
            }
        },
        "required": ["date"]
    }
)
def get_staff_schedule(date: str, staff_id: int = None) -> dict:
    """Get staff schedule for a date."""
    from datetime import datetime
    from apps.practice.models import Shift

    try:
        parsed_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return {'success': False, 'message': 'Invalid date format'}

    shifts = Shift.objects.filter(date=parsed_date).select_related('staff__user')
    if staff_id:
        shifts = shifts.filter(staff_id=staff_id)

    schedule = []
    for shift in shifts:
        schedule.append({
            'shift_id': shift.id,
            'staff_id': shift.staff.id,
            'staff_name': shift.staff.user.get_full_name() or shift.staff.user.username,
            'role': shift.staff.get_role_display(),
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M'),
            'is_confirmed': shift.is_confirmed,
            'notes': shift.notes,
        })

    return {
        'success': True,
        'date': date,
        'shifts': schedule,
        'total_staff': len(schedule),
    }


@tool(
    name="clock_in",
    description="Clock in a staff member",
    parameters={
        "type": "object",
        "properties": {
            "staff_id": {
                "type": "integer",
                "description": "Staff profile ID"
            },
            "notes": {
                "type": "string",
                "description": "Optional notes"
            }
        },
        "required": ["staff_id"]
    }
)
def clock_in(staff_id: int, notes: str = '') -> dict:
    """Clock in a staff member."""
    from django.utils import timezone
    from apps.practice.models import StaffProfile, TimeEntry

    try:
        staff = StaffProfile.objects.get(pk=staff_id)
    except StaffProfile.DoesNotExist:
        return {'success': False, 'message': 'Staff not found'}

    # Check for existing open time entry
    open_entry = TimeEntry.objects.filter(
        staff=staff,
        clock_out__isnull=True
    ).first()

    if open_entry:
        return {
            'success': False,
            'message': 'Already clocked in',
            'time_entry_id': open_entry.id
        }

    entry = TimeEntry.objects.create(
        staff=staff,
        clock_in=timezone.now(),
        notes=notes
    )

    return {
        'success': True,
        'time_entry_id': entry.id,
        'staff_name': staff.user.get_full_name() or staff.user.username,
        'clock_in_time': entry.clock_in.strftime('%Y-%m-%d %H:%M:%S')
    }


@tool(
    name="clock_out",
    description="Clock out a staff member",
    parameters={
        "type": "object",
        "properties": {
            "staff_id": {
                "type": "integer",
                "description": "Staff profile ID"
            },
            "break_minutes": {
                "type": "integer",
                "description": "Break time in minutes"
            }
        },
        "required": ["staff_id"]
    }
)
def clock_out(staff_id: int, break_minutes: int = 0) -> dict:
    """Clock out a staff member."""
    from django.utils import timezone
    from apps.practice.models import StaffProfile, TimeEntry

    try:
        staff = StaffProfile.objects.get(pk=staff_id)
    except StaffProfile.DoesNotExist:
        return {'success': False, 'message': 'Staff not found'}

    open_entry = TimeEntry.objects.filter(
        staff=staff,
        clock_out__isnull=True
    ).first()

    if not open_entry:
        return {'success': False, 'message': 'Not clocked in'}

    open_entry.clock_out = timezone.now()
    open_entry.break_minutes = break_minutes
    open_entry.save()

    return {
        'success': True,
        'time_entry_id': open_entry.id,
        'hours_worked': open_entry.hours_worked,
        'clock_in_time': open_entry.clock_in.strftime('%Y-%m-%d %H:%M:%S'),
        'clock_out_time': open_entry.clock_out.strftime('%Y-%m-%d %H:%M:%S'),
    }


@tool(
    name="create_clinical_note",
    description="Create a clinical note for a pet",
    parameters={
        "type": "object",
        "properties": {
            "pet_id": {
                "type": "integer",
                "description": "Pet ID"
            },
            "author_id": {
                "type": "integer",
                "description": "Author user ID"
            },
            "note_type": {
                "type": "string",
                "description": "Type: soap, progress, procedure, lab, phone, internal"
            },
            "subjective": {
                "type": "string",
                "description": "SOAP: Subjective findings"
            },
            "objective": {
                "type": "string",
                "description": "SOAP: Objective findings"
            },
            "assessment": {
                "type": "string",
                "description": "SOAP: Assessment"
            },
            "plan": {
                "type": "string",
                "description": "SOAP: Plan"
            },
            "content": {
                "type": "string",
                "description": "General content for non-SOAP notes"
            }
        },
        "required": ["pet_id", "author_id", "note_type"]
    }
)
def create_clinical_note(
    pet_id: int,
    author_id: int,
    note_type: str,
    subjective: str = '',
    objective: str = '',
    assessment: str = '',
    plan: str = '',
    content: str = ''
) -> dict:
    """Create a clinical note."""
    from apps.practice.models import ClinicalNote
    from apps.pets.models import Pet
    from apps.accounts.models import User

    try:
        pet = Pet.objects.get(pk=pet_id)
    except Pet.DoesNotExist:
        return {'success': False, 'message': 'Pet not found'}

    try:
        author = User.objects.get(pk=author_id)
    except User.DoesNotExist:
        return {'success': False, 'message': 'Author not found'}

    note = ClinicalNote.objects.create(
        pet=pet,
        author=author,
        note_type=note_type,
        subjective=subjective,
        objective=objective,
        assessment=assessment,
        plan=plan,
        content=content
    )

    return {
        'success': True,
        'note_id': note.id,
        'pet_name': pet.name,
        'note_type': note.get_note_type_display(),
        'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }


@tool(
    name="create_staff_task",
    description="Create a task for staff",
    parameters={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Task title"
            },
            "assigned_to_id": {
                "type": "integer",
                "description": "Staff profile ID to assign to"
            },
            "priority": {
                "type": "string",
                "description": "Priority: low, medium, high, urgent"
            },
            "description": {
                "type": "string",
                "description": "Task description"
            },
            "pet_id": {
                "type": "integer",
                "description": "Related pet ID"
            }
        },
        "required": ["title", "assigned_to_id"]
    }
)
def create_staff_task(
    title: str,
    assigned_to_id: int,
    priority: str = 'medium',
    description: str = '',
    pet_id: int = None
) -> dict:
    """Create a staff task."""
    from apps.practice.models import Task, StaffProfile
    from apps.pets.models import Pet

    try:
        assigned_to = StaffProfile.objects.get(pk=assigned_to_id)
    except StaffProfile.DoesNotExist:
        return {'success': False, 'message': 'Staff not found'}

    pet = None
    if pet_id:
        try:
            pet = Pet.objects.get(pk=pet_id)
        except Pet.DoesNotExist:
            return {'success': False, 'message': 'Pet not found'}

    task = Task.objects.create(
        title=title,
        description=description,
        assigned_to=assigned_to,
        priority=priority,
        pet=pet
    )

    return {
        'success': True,
        'task_id': task.id,
        'title': task.title,
        'assigned_to': assigned_to.user.get_full_name() or assigned_to.user.username,
        'priority': task.get_priority_display(),
        'status': task.get_status_display()
    }


# =============================================================================
# Reports & Analytics Tools
# =============================================================================

@tool(
    name="get_dashboard_metrics",
    description="Get key dashboard metrics for the clinic",
    parameters={
        "type": "object",
        "properties": {
            "period": {
                "type": "string",
                "description": "Period: today, week, month, year"
            }
        },
        "required": []
    }
)
def get_dashboard_metrics(period: str = 'month') -> dict:
    """Get dashboard metrics for specified period."""
    from datetime import date, timedelta
    from django.db.models import Sum, Count
    from apps.appointments.models import Appointment
    from apps.store.models import Order

    today = date.today()
    if period == 'today':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)

    appointments = Appointment.objects.filter(
        scheduled_date__gte=start_date,
        scheduled_date__lte=today
    )

    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=today
    )

    return {
        'success': True,
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': today.isoformat(),
        'metrics': {
            'total_appointments': appointments.count(),
            'completed_appointments': appointments.filter(status='completed').count(),
            'cancelled_appointments': appointments.filter(status='cancelled').count(),
            'total_orders': orders.count(),
            'order_revenue': float(orders.aggregate(Sum('total'))['total__sum'] or 0),
        }
    }


@tool(
    name="generate_report",
    description="Generate a report based on definition",
    parameters={
        "type": "object",
        "properties": {
            "report_type": {
                "type": "string",
                "description": "Report type: financial, operational, clinical"
            },
            "start_date": {
                "type": "string",
                "description": "Start date YYYY-MM-DD"
            },
            "end_date": {
                "type": "string",
                "description": "End date YYYY-MM-DD"
            }
        },
        "required": ["report_type"]
    }
)
def generate_report(
    report_type: str,
    start_date: str = None,
    end_date: str = None
) -> dict:
    """Generate a report."""
    from datetime import datetime, date, timedelta
    from django.db.models import Sum, Count, Avg
    from apps.appointments.models import Appointment
    from apps.store.models import Order

    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end = date.today()

    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start = end - timedelta(days=30)

    data = {
        'report_type': report_type,
        'period': {'start': start.isoformat(), 'end': end.isoformat()}
    }

    if report_type == 'financial':
        orders = Order.objects.filter(
            created_at__date__gte=start,
            created_at__date__lte=end
        )
        data['financial'] = {
            'total_revenue': float(orders.aggregate(Sum('total'))['total__sum'] or 0),
            'total_orders': orders.count(),
            'average_order': float(orders.aggregate(Avg('total'))['total__avg'] or 0),
        }
    elif report_type == 'operational':
        appointments = Appointment.objects.filter(
            scheduled_date__gte=start,
            scheduled_date__lte=end
        )
        data['operational'] = {
            'total_appointments': appointments.count(),
            'completed': appointments.filter(status='completed').count(),
            'no_show': appointments.filter(status='no_show').count(),
            'utilization_rate': 0,
        }

    return {'success': True, 'report': data}


@tool(
    name="get_analytics_summary",
    description="Get analytics summary for the clinic",
    parameters={
        "type": "object",
        "properties": {
            "metric": {
                "type": "string",
                "description": "Metric to analyze: revenue, appointments, pets"
            },
            "days": {
                "type": "integer",
                "description": "Number of days to analyze"
            }
        },
        "required": []
    }
)
def get_analytics_summary(metric: str = 'revenue', days: int = 30) -> dict:
    """Get analytics summary."""
    from datetime import date, timedelta
    from apps.reports.models import MetricSnapshot

    start_date = date.today() - timedelta(days=days)

    snapshots = MetricSnapshot.objects.filter(
        metric_name=metric,
        date__gte=start_date
    ).order_by('date')

    trend_data = [
        {'date': s.date.isoformat(), 'value': float(s.metric_value)}
        for s in snapshots
    ]

    total = sum(item['value'] for item in trend_data)
    avg = total / len(trend_data) if trend_data else 0

    return {
        'success': True,
        'metric': metric,
        'days': days,
        'summary': {
            'total': round(total, 2),
            'average': round(avg, 2),
            'data_points': len(trend_data),
        },
        'trend': trend_data[:10]  # Return last 10 for brevity
    }


# =============================================================================
# Accounting Tools
# =============================================================================

@tool(
    name="get_chart_account_balance",
    description="Get balance for a chart of accounts entry",
    parameters={
        "type": "object",
        "properties": {
            "account_code": {
                "type": "string",
                "description": "Account code (e.g., 1000)"
            }
        },
        "required": ["account_code"]
    }
)
def get_chart_account_balance(account_code: str) -> dict:
    """Get chart of accounts balance."""
    from apps.accounting.models import Account

    try:
        account = Account.objects.get(code=account_code)
    except Account.DoesNotExist:
        return {'success': False, 'message': 'Account not found'}

    return {
        'success': True,
        'account': {
            'code': account.code,
            'name': account.name,
            'type': account.get_account_type_display(),
            'balance': float(account.balance),
            'is_active': account.is_active,
        }
    }


@tool(
    name="get_financial_summary",
    description="Get financial summary for the clinic",
    parameters={
        "type": "object",
        "properties": {
            "period": {
                "type": "string",
                "description": "Period: month, quarter, year"
            }
        },
        "required": []
    }
)
def get_financial_summary(period: str = 'month') -> dict:
    """Get financial summary."""
    from django.db.models import Sum
    from apps.accounting.models import Account

    assets = Account.objects.filter(
        account_type='asset',
        is_active=True
    ).aggregate(total=Sum('balance'))['total'] or 0

    liabilities = Account.objects.filter(
        account_type='liability',
        is_active=True
    ).aggregate(total=Sum('balance'))['total'] or 0

    equity = Account.objects.filter(
        account_type='equity',
        is_active=True
    ).aggregate(total=Sum('balance'))['total'] or 0

    revenue = Account.objects.filter(
        account_type='revenue',
        is_active=True
    ).aggregate(total=Sum('balance'))['total'] or 0

    expenses = Account.objects.filter(
        account_type='expense',
        is_active=True
    ).aggregate(total=Sum('balance'))['total'] or 0

    return {
        'success': True,
        'period': period,
        'summary': {
            'total_assets': float(assets),
            'total_liabilities': float(liabilities),
            'total_equity': float(equity),
            'total_revenue': float(revenue),
            'total_expenses': float(expenses),
            'net_income': float(revenue - expenses),
        }
    }


@tool(
    name="record_expense",
    description="Record an expense/bill",
    parameters={
        "type": "object",
        "properties": {
            "vendor_name": {
                "type": "string",
                "description": "Vendor name"
            },
            "amount": {
                "type": "number",
                "description": "Expense amount"
            },
            "description": {
                "type": "string",
                "description": "Expense description"
            },
            "expense_account_code": {
                "type": "string",
                "description": "Expense account code"
            }
        },
        "required": ["vendor_name", "amount", "description"]
    }
)
def record_expense(
    vendor_name: str,
    amount: float,
    description: str,
    expense_account_code: str = '5000'
) -> dict:
    """Record an expense."""
    from decimal import Decimal
    from datetime import date
    from apps.accounting.models import Vendor, Bill, BillLine, Account

    vendor, _ = Vendor.objects.get_or_create(
        name=vendor_name,
        defaults={'email': ''}
    )

    try:
        expense_account = Account.objects.get(code=expense_account_code)
    except Account.DoesNotExist:
        expense_account = Account.objects.create(
            code=expense_account_code,
            name='General Expenses',
            account_type='expense'
        )

    tax = Decimal(str(amount)) * Decimal('0.16')
    total = Decimal(str(amount)) + tax

    bill = Bill.objects.create(
        vendor=vendor,
        bill_number=f"EXP-{date.today().strftime('%Y%m%d')}-{Bill.objects.count() + 1}",
        bill_date=date.today(),
        due_date=date.today(),
        subtotal=Decimal(str(amount)),
        tax=tax,
        total=total,
        status='pending',
    )

    BillLine.objects.create(
        bill=bill,
        description=description,
        quantity=1,
        unit_price=Decimal(str(amount)),
        amount=Decimal(str(amount)),
        expense_account=expense_account,
    )

    return {
        'success': True,
        'bill_id': bill.id,
        'bill_number': bill.bill_number,
        'vendor': vendor.name,
        'total': float(bill.total),
        'status': bill.get_status_display(),
    }


@tool(
    name="get_accounts_payable",
    description="Get outstanding bills/accounts payable",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_accounts_payable() -> dict:
    """Get accounts payable summary."""
    from django.db.models import Sum
    from apps.accounting.models import Bill

    pending = Bill.objects.filter(status__in=['pending', 'partial'])

    total_due = sum(b.balance_due for b in pending)

    bills = [
        {
            'bill_id': b.id,
            'vendor': b.vendor.name,
            'bill_number': b.bill_number,
            'due_date': b.due_date.isoformat(),
            'total': float(b.total),
            'paid': float(b.amount_paid),
            'balance_due': float(b.balance_due),
        }
        for b in pending[:10]
    ]

    return {
        'success': True,
        'total_outstanding': float(total_due),
        'bill_count': pending.count(),
        'bills': bills,
    }

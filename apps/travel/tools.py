"""AI tools for travel certificates."""
from datetime import datetime, timedelta
from typing import Optional

from apps.pets.models import Pet, Vaccination
from .models import TravelDestination, HealthCertificate


def check_travel_requirements(pet_id: int, destination_id: int, travel_date: str) -> dict:
    """
    Check travel requirements for a pet to a destination.

    Args:
        pet_id: The pet's ID
        destination_id: The destination country ID
        travel_date: Travel date in ISO format (YYYY-MM-DD)

    Returns:
        Dict with requirements status and any missing items
    """
    try:
        pet = Pet.objects.get(pk=pet_id)
    except Pet.DoesNotExist:
        return {
            'success': False,
            'error': 'Pet not found'
        }

    try:
        destination = TravelDestination.objects.get(pk=destination_id, is_active=True)
    except TravelDestination.DoesNotExist:
        return {
            'success': False,
            'error': 'Destination not found'
        }

    try:
        travel_dt = datetime.strptime(travel_date, '%Y-%m-%d').date()
    except ValueError:
        return {
            'success': False,
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }

    requirements_status = {}
    missing_requirements = []

    for req_type, req_details in destination.requirements.items():
        status = {
            'required': req_details.get('required', False),
            'description': req_details.get('description', ''),
            'met': False,
            'notes': ''
        }

        if req_type == 'rabies_vaccine':
            days_before = req_details.get('days_before', 30)
            cutoff_date = travel_dt - timedelta(days=days_before)

            rabies_vaccines = Vaccination.objects.filter(
                pet=pet,
                vaccine_name__icontains='rabies',
                date_administered__lte=cutoff_date
            ).order_by('-date_administered')

            if rabies_vaccines.exists():
                vaccine = rabies_vaccines.first()
                if vaccine.next_due_date is None or vaccine.next_due_date > travel_dt:
                    status['met'] = True
                    status['notes'] = f'Rabies vaccine administered {vaccine.date_administered}'
                else:
                    status['notes'] = f'Rabies vaccine expired on {vaccine.next_due_date}'
            else:
                status['notes'] = f'No rabies vaccine found administered at least {days_before} days before travel'

        elif req_type == 'microchip':
            if pet.microchip_id:
                status['met'] = True
                status['notes'] = f'Microchip ID: {pet.microchip_id}'
            else:
                status['notes'] = 'No microchip ID registered'

        elif req_type == 'health_exam':
            status['notes'] = 'Veterinary examination required before travel'

        if status['required'] and not status['met']:
            missing_requirements.append({
                'type': req_type,
                'description': status['description']
            })

        requirements_status[req_type] = status

    return {
        'success': True,
        'pet': {
            'id': pet.pk,
            'name': pet.name,
            'species': pet.species,
            'microchip_id': pet.microchip_id
        },
        'destination': {
            'id': destination.pk,
            'country': destination.country_name,
            'validity_days': destination.certificate_validity_days
        },
        'travel_date': travel_date,
        'requirements': requirements_status,
        'missing_requirements': missing_requirements,
        'ready_to_travel': len(missing_requirements) == 0
    }


def get_destination_requirements(destination_id: int) -> dict:
    """
    Get requirements for a specific destination.

    Args:
        destination_id: The destination country ID

    Returns:
        Dict with destination details and requirements
    """
    try:
        destination = TravelDestination.objects.get(pk=destination_id, is_active=True)

        return {
            'success': True,
            'id': destination.pk,
            'country': destination.country_name,
            'country_code': destination.country_code,
            'requirements': destination.requirements,
            'certificate_validity_days': destination.certificate_validity_days,
            'quarantine_required': destination.quarantine_required,
            'quarantine_days': destination.quarantine_days,
            'airline_requirements': destination.airline_requirements,
            'notes': destination.notes
        }

    except TravelDestination.DoesNotExist:
        return {
            'success': False,
            'error': 'Destination not found'
        }


def list_destinations(search: Optional[str] = None) -> dict:
    """
    List available travel destinations.

    Args:
        search: Optional search term for country name

    Returns:
        Dict with list of destinations
    """
    qs = TravelDestination.objects.filter(is_active=True)

    if search:
        qs = qs.filter(country_name__icontains=search)

    destinations = []
    for dest in qs.order_by('country_name'):
        destinations.append({
            'id': dest.pk,
            'country': dest.country_name,
            'country_code': dest.country_code,
            'quarantine_required': dest.quarantine_required,
            'certificate_validity_days': dest.certificate_validity_days
        })

    return {
        'success': True,
        'destinations': destinations,
        'total': len(destinations)
    }


def get_pet_certificates(pet_id: int) -> dict:
    """
    Get health certificates for a pet.

    Args:
        pet_id: The pet's ID

    Returns:
        Dict with list of certificates
    """
    try:
        pet = Pet.objects.get(pk=pet_id)
    except Pet.DoesNotExist:
        return {
            'success': False,
            'error': 'Pet not found'
        }

    certificates = []
    for cert in HealthCertificate.objects.filter(pet=pet).select_related('destination'):
        certificates.append({
            'id': cert.pk,
            'destination': cert.destination.country_name,
            'travel_date': str(cert.travel_date),
            'issue_date': str(cert.issue_date) if cert.issue_date else None,
            'expiry_date': str(cert.expiry_date) if cert.expiry_date else None,
            'status': cert.status,
            'certificate_number': cert.certificate_number
        })

    return {
        'success': True,
        'pet': {
            'id': pet.pk,
            'name': pet.name
        },
        'certificates': certificates,
        'total': len(certificates)
    }

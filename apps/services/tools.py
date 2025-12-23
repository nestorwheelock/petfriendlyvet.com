"""AI tools for external services."""
from typing import Optional

from .models import ExternalPartner


def list_partners(partner_type: Optional[str] = None) -> dict:
    """
    List external service partners.

    Args:
        partner_type: Optional filter by type (grooming, boarding, etc.)

    Returns:
        Dict with success status and list of partners
    """
    qs = ExternalPartner.objects.filter(is_active=True)

    if partner_type:
        qs = qs.filter(partner_type=partner_type)

    partners = []
    for partner in qs.order_by('-is_preferred', 'name'):
        partners.append({
            'id': partner.pk,
            'name': partner.name,
            'type': partner.get_partner_type_display(),
            'phone': partner.phone,
            'email': partner.email,
            'address': partner.address,
            'is_preferred': partner.is_preferred,
            'average_rating': float(partner.average_rating) if partner.average_rating else None
        })

    return {
        'success': True,
        'partners': partners,
        'total': len(partners)
    }


def get_partner_details(partner_id: int) -> dict:
    """
    Get details for a specific partner.

    Args:
        partner_id: The partner's ID

    Returns:
        Dict with partner details or error
    """
    try:
        partner = ExternalPartner.objects.get(pk=partner_id, is_active=True)

        return {
            'success': True,
            'partner': {
                'id': partner.pk,
                'name': partner.name,
                'type': partner.get_partner_type_display(),
                'contact_name': partner.contact_name,
                'phone': partner.phone,
                'email': partner.email,
                'website': partner.website,
                'address': partner.address,
                'description': partner.description,
                'services_offered': partner.services_offered,
                'hours_of_operation': partner.hours_of_operation,
                'price_range': partner.price_range,
                'is_preferred': partner.is_preferred,
                'average_rating': float(partner.average_rating) if partner.average_rating else None
            }
        }

    except ExternalPartner.DoesNotExist:
        return {
            'success': False,
            'error': 'Partner not found'
        }

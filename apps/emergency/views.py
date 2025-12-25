"""Emergency app views for customer-facing pages."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import (
    EmergencyContact,
    EmergencyFirstAid,
    EmergencyReferral,
    EmergencySymptom,
)


def emergency_home(request):
    """Emergency landing page with quick access to all emergency resources."""
    return render(request, 'emergency/home.html')


def triage_form(request):
    """Self-triage form - describe symptoms to assess severity."""
    if request.method == 'POST':
        species = request.POST.get('species', '')
        symptoms_text = request.POST.get('symptoms', '')

        # Simple keyword matching for triage
        severity = None
        matched_symptoms = []
        first_aid_tips = []

        if symptoms_text:
            symptoms_lower = symptoms_text.lower()
            all_symptoms = EmergencySymptom.objects.filter(is_active=True)

            for symptom in all_symptoms:
                # Check main keyword
                if symptom.keyword.lower() in symptoms_lower:
                    matched_symptoms.append(symptom)
                    continue
                # Check Spanish keywords
                for kw in symptom.keywords_es:
                    if kw.lower() in symptoms_lower:
                        matched_symptoms.append(symptom)
                        break
                # Check English keywords
                for kw in symptom.keywords_en:
                    if kw.lower() in symptoms_lower:
                        matched_symptoms.append(symptom)
                        break

            # Determine severity from matched symptoms
            if matched_symptoms:
                severities = [s.severity for s in matched_symptoms]
                if 'critical' in severities:
                    severity = 'critical'
                elif 'urgent' in severities:
                    severity = 'urgent'
                elif 'moderate' in severities:
                    severity = 'moderate'
                else:
                    severity = 'low'

                # Get first aid tips from matched symptoms
                for symptom in matched_symptoms:
                    if symptom.first_aid_instructions:
                        first_aid_tips.append({
                            'symptom': symptom.keyword,
                            'instructions': symptom.first_aid_instructions,
                            'warning_signs': symptom.warning_signs,
                        })

        # Store in session for result page
        request.session['triage_result'] = {
            'species': species,
            'symptoms': symptoms_text,
            'severity': severity,
            'matched_symptoms': [s.keyword for s in matched_symptoms],
            'first_aid_tips': first_aid_tips,
        }

        return redirect('emergency:triage_result')

    species_choices = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('rabbit', 'Rabbit'),
        ('other', 'Other'),
    ]

    context = {
        'species_choices': species_choices,
    }
    return render(request, 'emergency/triage_form.html', context)


def triage_result(request):
    """Display triage assessment result."""
    result = request.session.get('triage_result')

    if not result:
        return redirect('emergency:triage')

    severity_info = {
        'critical': {
            'class': 'bg-red-100 text-red-800 border-red-500',
            'icon': '🚨',
            'title': 'Critical Emergency',
            'message': 'Seek immediate veterinary care. Call us or go to the nearest '
                       '24-hour emergency hospital NOW.',
        },
        'urgent': {
            'class': 'bg-orange-100 text-orange-800 border-orange-500',
            'icon': '⚠️',
            'title': 'Urgent Care Needed',
            'message': 'Your pet needs veterinary attention today. Contact us to '
                       'schedule an urgent appointment.',
        },
        'moderate': {
            'class': 'bg-yellow-100 text-yellow-800 border-yellow-500',
            'icon': '📋',
            'title': 'Monitor & Schedule',
            'message': 'Keep an eye on your pet. Schedule an appointment within '
                       'the next few days.',
        },
        'low': {
            'class': 'bg-green-100 text-green-800 border-green-500',
            'icon': '✓',
            'title': 'Low Concern',
            'message': 'This may not require immediate attention, but schedule a '
                       'check-up if symptoms persist.',
        },
    }

    context = {
        'result': result,
        'severity_info': severity_info.get(result.get('severity'), {}),
        'hospitals': EmergencyReferral.objects.filter(
            is_active=True, is_24_hours=True
        )[:3],
    }
    return render(request, 'emergency/triage_result.html', context)


def first_aid_list(request):
    """List of first aid guides for common emergencies."""
    guides = EmergencyFirstAid.objects.filter(is_active=True)

    # Filter by species if provided
    species = request.GET.get('species')
    if species:
        guides = [g for g in guides if species in g.species]

    context = {
        'guides': guides,
        'species_filter': species,
    }
    return render(request, 'emergency/first_aid_list.html', context)


def first_aid_detail(request, pk):
    """Detailed first aid instructions."""
    guide = get_object_or_404(EmergencyFirstAid, pk=pk, is_active=True)

    context = {
        'guide': guide,
    }
    return render(request, 'emergency/first_aid_detail.html', context)


def hospital_list(request):
    """List of emergency hospitals and referral centers."""
    hospitals = EmergencyReferral.objects.filter(is_active=True)

    # Filter by 24-hours only
    if request.GET.get('24hours'):
        hospitals = hospitals.filter(is_24_hours=True)

    context = {
        'hospitals': hospitals,
        'filter_24hours': request.GET.get('24hours'),
    }
    return render(request, 'emergency/hospital_list.html', context)


def emergency_contact(request):
    """Submit emergency contact request."""
    if request.method == 'POST':
        phone = request.POST.get('phone', '')
        pet_species = request.POST.get('species', '')
        pet_age = request.POST.get('age', '')
        symptoms = request.POST.get('symptoms', '')
        channel = request.POST.get('channel', 'web')

        # Create emergency contact record
        contact = EmergencyContact.objects.create(
            owner=request.user if request.user.is_authenticated else None,
            phone=phone,
            channel=channel,
            reported_symptoms=symptoms,
            pet_species=pet_species,
            pet_age=pet_age,
            status='initiated',
        )

        # Store contact ID for success page
        request.session['emergency_contact_id'] = contact.pk

        messages.success(
            request,
            'Your emergency request has been submitted. We will contact you shortly.'
        )
        return redirect('emergency:contact_success')

    context = {
        'species_choices': [
            ('dog', 'Dog'),
            ('cat', 'Cat'),
            ('bird', 'Bird'),
            ('rabbit', 'Rabbit'),
            ('other', 'Other'),
        ],
    }
    return render(request, 'emergency/contact_form.html', context)


def contact_success(request):
    """Emergency contact submission success page."""
    contact_id = request.session.get('emergency_contact_id')
    contact = None

    if contact_id:
        try:
            contact = EmergencyContact.objects.get(pk=contact_id)
        except EmergencyContact.DoesNotExist:
            pass

    context = {
        'contact': contact,
        'hospitals': EmergencyReferral.objects.filter(
            is_active=True, is_24_hours=True
        )[:3],
    }
    return render(request, 'emergency/contact_success.html', context)


@login_required
def emergency_history(request):
    """View past emergency contacts for authenticated user."""
    contacts = EmergencyContact.objects.filter(owner=request.user)

    context = {
        'contacts': contacts,
    }
    return render(request, 'emergency/history.html', context)

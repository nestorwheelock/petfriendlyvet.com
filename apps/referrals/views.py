"""Referral network views."""
from datetime import date, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404

from .models import Specialist, Referral, VisitingSchedule, VisitingAppointment


@staff_member_required
def dashboard(request):
    """Referral network dashboard."""
    # Summary stats
    active_specialists = Specialist.objects.filter(
        is_active=True, relationship_status='active'
    ).count()

    pending_referrals = Referral.objects.filter(
        status__in=['draft', 'sent', 'received']
    ).count()

    upcoming_visits = VisitingSchedule.objects.filter(
        date__gte=date.today(),
        status__in=['scheduled', 'confirmed']
    ).count()

    completed_this_month = Referral.objects.filter(
        status='completed',
        completed_at__month=date.today().month,
        completed_at__year=date.today().year
    ).count()

    # Recent referrals
    recent_referrals = Referral.objects.select_related(
        'pet', 'owner', 'specialist'
    ).order_by('-created_at')[:5]

    # Upcoming visiting specialists
    upcoming_schedules = VisitingSchedule.objects.filter(
        date__gte=date.today(),
        status__in=['scheduled', 'confirmed']
    ).select_related('specialist').order_by('date', 'start_time')[:5]

    context = {
        'active_specialists': active_specialists,
        'pending_referrals': pending_referrals,
        'upcoming_visits': upcoming_visits,
        'completed_this_month': completed_this_month,
        'recent_referrals': recent_referrals,
        'upcoming_schedules': upcoming_schedules,
    }
    return render(request, 'referrals/dashboard.html', context)


@staff_member_required
def specialist_list(request):
    """List all specialists."""
    specialty = request.GET.get('specialty', '')
    visiting = request.GET.get('visiting', '')

    specialists = Specialist.objects.filter(is_active=True)

    if specialty:
        specialists = specialists.filter(specialty=specialty)
    if visiting == 'yes':
        specialists = specialists.filter(is_visiting=True)
    elif visiting == 'no':
        specialists = specialists.filter(is_visiting=False)

    specialists = specialists.order_by('name')

    context = {
        'specialists': specialists,
        'specialty_choices': Specialist.SPECIALIST_TYPES,
        'current_specialty': specialty,
        'current_visiting': visiting,
    }
    return render(request, 'referrals/specialist_list.html', context)


@staff_member_required
def specialist_detail(request, pk):
    """View specialist details."""
    specialist = get_object_or_404(Specialist, pk=pk)

    # Recent referrals to this specialist
    recent_referrals = specialist.referrals_received.select_related(
        'pet', 'owner'
    ).order_by('-created_at')[:5]

    # Upcoming visits
    upcoming_visits = specialist.visiting_schedules.filter(
        date__gte=date.today(),
        status__in=['scheduled', 'confirmed']
    ).order_by('date', 'start_time')[:5]

    context = {
        'specialist': specialist,
        'recent_referrals': recent_referrals,
        'upcoming_visits': upcoming_visits,
    }
    return render(request, 'referrals/specialist_detail.html', context)


@staff_member_required
def referral_list(request):
    """List referrals."""
    status = request.GET.get('status', '')
    direction = request.GET.get('direction', '')

    referrals = Referral.objects.select_related('pet', 'owner', 'specialist')

    if status:
        referrals = referrals.filter(status=status)
    if direction:
        referrals = referrals.filter(direction=direction)

    referrals = referrals.order_by('-created_at')[:50]

    context = {
        'referrals': referrals,
        'status_choices': Referral.STATUS_CHOICES,
        'direction_choices': Referral.DIRECTION_CHOICES,
        'current_status': status,
        'current_direction': direction,
    }
    return render(request, 'referrals/referral_list.html', context)


@staff_member_required
def referral_detail(request, pk):
    """View referral details."""
    referral = get_object_or_404(
        Referral.objects.select_related(
            'pet', 'owner', 'specialist', 'referred_by'
        ),
        pk=pk
    )

    # Get documents and notes
    documents = referral.documents.order_by('-uploaded_at')
    notes = referral.notes_list.order_by('-created_at')

    context = {
        'referral': referral,
        'documents': documents,
        'notes': notes,
    }
    return render(request, 'referrals/referral_detail.html', context)


@staff_member_required
def visiting_schedule(request):
    """View visiting specialist schedules."""
    period = request.GET.get('period', 'upcoming')
    today = date.today()

    schedules = VisitingSchedule.objects.select_related('specialist')

    if period == 'today':
        schedules = schedules.filter(date=today)
    elif period == 'week':
        week_end = today + timedelta(days=7)
        schedules = schedules.filter(date__gte=today, date__lte=week_end)
    elif period == 'upcoming':
        schedules = schedules.filter(date__gte=today)
    elif period == 'past':
        schedules = schedules.filter(date__lt=today)

    schedules = schedules.order_by('date', 'start_time')[:50]

    context = {
        'schedules': schedules,
        'current_period': period,
    }
    return render(request, 'referrals/visiting_schedule.html', context)


@staff_member_required
def visiting_detail(request, pk):
    """View visiting schedule details."""
    schedule = get_object_or_404(
        VisitingSchedule.objects.select_related('specialist'),
        pk=pk
    )

    # Get appointments for this schedule
    appointments = schedule.appointments.select_related(
        'pet', 'owner'
    ).order_by('appointment_time')

    context = {
        'schedule': schedule,
        'appointments': appointments,
    }
    return render(request, 'referrals/visiting_detail.html', context)

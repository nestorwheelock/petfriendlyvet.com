"""Location management views for staff portal."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.accounts.decorators import require_permission

from .forms import ExamRoomForm
from .models import ExamRoom, Location


def staff_required(view_func):
    """Decorator requiring staff access."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("Staff access required")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@require_permission('locations', 'view')
def location_list(request):
    """List all locations."""
    locations = Location.objects.filter(is_active=True).order_by('name')

    # Annotate with room counts
    for loc in locations:
        loc.active_room_count = loc.exam_rooms.filter(is_active=True).count()
        loc.total_room_count = loc.exam_rooms.count()

    return render(request, 'locations/location_list.html', {
        'locations': locations,
    })


@login_required
@require_permission('locations', 'view')
def room_list(request, location_id):
    """List exam rooms for a location."""
    location = get_object_or_404(Location, id=location_id)

    show_inactive = request.GET.get('show_inactive') == '1'

    if show_inactive:
        rooms = location.exam_rooms.all()
    else:
        rooms = location.exam_rooms.filter(is_active=True)

    rooms = rooms.order_by('display_order', 'name')

    inactive_count = location.exam_rooms.filter(is_active=False).count()

    return render(request, 'locations/room_list.html', {
        'location': location,
        'rooms': rooms,
        'show_inactive': show_inactive,
        'inactive_count': inactive_count,
    })


@login_required
@require_permission('locations', 'edit')
def room_create(request, location_id):
    """Create a new exam room."""
    location = get_object_or_404(Location, id=location_id)

    if request.method == 'POST':
        form = ExamRoomForm(request.POST, location=location)
        if form.is_valid():
            room = form.save(commit=False)
            room.location = location
            room.save()
            messages.success(request, _('Exam room created successfully.'))
            return redirect('locations:room_list', location_id=location.id)
    else:
        form = ExamRoomForm(location=location)

    return render(request, 'locations/room_form.html', {
        'form': form,
        'location': location,
        'is_edit': False,
    })


@login_required
@require_permission('locations', 'edit')
def room_edit(request, location_id, room_id):
    """Edit an exam room."""
    location = get_object_or_404(Location, id=location_id)
    room = get_object_or_404(ExamRoom, id=room_id, location=location)

    if request.method == 'POST':
        form = ExamRoomForm(request.POST, instance=room, location=location)
        if form.is_valid():
            form.save()
            messages.success(request, _('Exam room updated successfully.'))
            return redirect('locations:room_list', location_id=location.id)
    else:
        form = ExamRoomForm(instance=room, location=location)

    return render(request, 'locations/room_form.html', {
        'form': form,
        'location': location,
        'room': room,
        'is_edit': True,
    })


@login_required
@require_permission('locations', 'edit')
@require_POST
def room_deactivate(request, location_id, room_id):
    """Deactivate (soft-delete) an exam room."""
    location = get_object_or_404(Location, id=location_id)
    room = get_object_or_404(ExamRoom, id=room_id, location=location)

    room.is_active = False
    room.save()

    messages.success(request, _('Exam room "%(name)s" has been deactivated.') % {'name': room.name})
    return redirect('locations:room_list', location_id=location.id)


@login_required
@require_permission('locations', 'edit')
@require_POST
def room_reactivate(request, location_id, room_id):
    """Reactivate an exam room."""
    location = get_object_or_404(Location, id=location_id)
    room = get_object_or_404(ExamRoom, id=room_id, location=location)

    room.is_active = True
    room.save()

    messages.success(request, _('Exam room "%(name)s" has been reactivated.') % {'name': room.name})
    return redirect('locations:room_list', location_id=location.id)

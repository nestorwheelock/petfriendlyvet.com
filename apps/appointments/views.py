"""Appointment booking views."""
from datetime import datetime, timedelta
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, DetailView, CreateView, TemplateView

from .models import Appointment, ServiceType, ScheduleBlock


class AppointmentBookingForm(forms.ModelForm):
    """Form for booking an appointment."""

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'min': datetime.now().strftime('%Y-%m-%d'),
        })
    )
    time_slot = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
        })
    )

    class Meta:
        model = Appointment
        fields = ['pet', 'service', 'notes']
        widgets = {
            'pet': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            }),
            'service': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'rows': 3,
                'placeholder': _('Any additional notes or concerns...'),
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Filter pets to user's pets
        if user:
            self.fields['pet'].queryset = user.pets.all()

        # Filter to active services
        self.fields['service'].queryset = ServiceType.objects.filter(is_active=True)

        # Generate time slots
        self.fields['time_slot'].choices = self._generate_time_slots()

    def _generate_time_slots(self):
        """Generate available time slots."""
        slots = [('', _('Select a time'))]
        start_hour = 9
        end_hour = 18

        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                time_str = f'{hour:02d}:{minute:02d}'
                display = f'{hour:02d}:{minute:02d}'
                if hour < 12:
                    display += ' AM'
                elif hour == 12:
                    display += ' PM'
                else:
                    display = f'{hour-12:02d}:{minute:02d} PM'
                slots.append((time_str, display))

        return slots


class ServiceListView(ListView):
    """List available services for booking."""

    model = ServiceType
    template_name = 'appointments/service_list.html'
    context_object_name = 'services'

    def get_queryset(self):
        return ServiceType.objects.filter(is_active=True).order_by('category', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Group by category
        services_by_category = {}
        for service in context['services']:
            cat = service.get_category_display()
            if cat not in services_by_category:
                services_by_category[cat] = []
            services_by_category[cat].append(service)
        context['services_by_category'] = services_by_category
        return context


class BookAppointmentView(LoginRequiredMixin, CreateView):
    """Book a new appointment."""

    model = Appointment
    form_class = AppointmentBookingForm
    template_name = 'appointments/book_appointment.html'
    success_url = reverse_lazy('appointments:my_appointments')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select service if passed in URL
        service_id = self.request.GET.get('service')
        if service_id:
            initial['service'] = service_id
        return initial

    def form_valid(self, form):
        # Set the owner
        form.instance.owner = self.request.user

        # Parse date and time
        date = form.cleaned_data['date']
        time_str = form.cleaned_data['time_slot']
        hour, minute = map(int, time_str.split(':'))

        # Create datetime
        scheduled_start = timezone.make_aware(
            datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
        )

        # Calculate end time based on service duration
        service = form.cleaned_data['service']
        scheduled_end = scheduled_start + timedelta(minutes=service.duration_minutes)

        form.instance.scheduled_start = scheduled_start
        form.instance.scheduled_end = scheduled_end

        messages.success(self.request, _('Your appointment has been booked successfully!'))
        return super().form_valid(form)


class MyAppointmentsView(LoginRequiredMixin, ListView):
    """List user's appointments."""

    model = Appointment
    template_name = 'appointments/my_appointments.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        return Appointment.objects.filter(
            owner=self.request.user
        ).select_related('pet', 'service', 'veterinarian').order_by('-scheduled_start')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # Separate upcoming and past
        context['upcoming'] = [a for a in context['appointments'] if a.scheduled_start > now]
        context['past'] = [a for a in context['appointments'] if a.scheduled_start <= now]

        return context


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    """View appointment details."""

    model = Appointment
    template_name = 'appointments/appointment_detail.html'
    context_object_name = 'appointment'

    def get_queryset(self):
        return Appointment.objects.filter(
            owner=self.request.user
        ).select_related('pet', 'service', 'veterinarian')


class CancelAppointmentView(LoginRequiredMixin, TemplateView):
    """Cancel an appointment."""

    template_name = 'appointments/cancel_appointment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['appointment'] = get_object_or_404(
            Appointment,
            pk=self.kwargs['pk'],
            owner=self.request.user
        )
        return context

    def post(self, request, *args, **kwargs):
        appointment = get_object_or_404(
            Appointment,
            pk=self.kwargs['pk'],
            owner=request.user
        )

        reason = request.POST.get('reason', '')

        appointment.status = 'cancelled'
        appointment.cancelled_at = timezone.now()
        appointment.cancellation_reason = reason
        appointment.save()

        messages.info(request, _('Your appointment has been cancelled.'))
        return redirect('appointments:my_appointments')


class AvailableSlotsView(LoginRequiredMixin, TemplateView):
    """AJAX view to get available time slots for a date."""

    template_name = 'appointments/partials/time_slots.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        date_str = self.request.GET.get('date')
        service_id = self.request.GET.get('service')

        if date_str and service_id:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                service = ServiceType.objects.get(pk=service_id)

                # Get available slots (simplified - in production check existing bookings)
                slots = []
                for hour in range(9, 18):
                    for minute in [0, 30]:
                        time_str = f'{hour:02d}:{minute:02d}'
                        slots.append({
                            'value': time_str,
                            'display': f'{hour:02d}:{minute:02d}',
                            'available': True,  # In production, check availability
                        })

                context['slots'] = slots
            except (ValueError, ServiceType.DoesNotExist):
                context['slots'] = []

        return context


class RescheduleAppointmentForm(forms.Form):
    """Form for rescheduling an appointment."""

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
        })
    )
    time_slot = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
        })
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'rows': 2,
            'placeholder': _('Reason for rescheduling (optional)'),
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set minimum date to today
        self.fields['date'].widget.attrs['min'] = datetime.now().strftime('%Y-%m-%d')
        # Generate time slots
        self.fields['time_slot'].choices = self._generate_time_slots()

    def _generate_time_slots(self):
        """Generate available time slots."""
        slots = [('', _('Select a time'))]
        for hour in range(9, 18):
            for minute in [0, 30]:
                time_str = f'{hour:02d}:{minute:02d}'
                if hour < 12:
                    display = f'{hour:02d}:{minute:02d} AM'
                elif hour == 12:
                    display = f'12:{minute:02d} PM'
                else:
                    display = f'{hour-12:02d}:{minute:02d} PM'
                slots.append((time_str, display))
        return slots


class RescheduleAppointmentView(LoginRequiredMixin, TemplateView):
    """Reschedule an appointment to a new date/time."""

    template_name = 'appointments/reschedule_appointment.html'

    def get_appointment(self):
        return get_object_or_404(
            Appointment,
            pk=self.kwargs['pk'],
            owner=self.request.user,
            status__in=['scheduled', 'confirmed']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment = self.get_appointment()
        context['appointment'] = appointment

        # Initialize form with current date/time
        initial = {
            'date': appointment.scheduled_start.date(),
            'time_slot': appointment.scheduled_start.strftime('%H:%M'),
        }
        context['form'] = RescheduleAppointmentForm(initial=initial)
        return context

    def post(self, request, *args, **kwargs):
        appointment = self.get_appointment()
        form = RescheduleAppointmentForm(request.POST)

        if form.is_valid():
            # Store old time for reference
            old_time = appointment.scheduled_start

            # Parse new date and time
            date = form.cleaned_data['date']
            time_str = form.cleaned_data['time_slot']
            hour, minute = map(int, time_str.split(':'))

            # Create new datetime
            new_start = timezone.make_aware(
                datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
            )

            # Calculate new end time based on service duration
            new_end = new_start + timedelta(minutes=appointment.service.duration_minutes)

            # Update appointment
            appointment.scheduled_start = new_start
            appointment.scheduled_end = new_end
            appointment.status = 'scheduled'  # Reset to scheduled
            appointment.reminder_sent = False  # Reset reminder
            appointment.save()

            messages.success(
                request,
                _('Your appointment has been rescheduled from %(old_date)s to %(new_date)s.') % {
                    'old_date': old_time.strftime('%b %d, %Y %H:%M'),
                    'new_date': new_start.strftime('%b %d, %Y %H:%M'),
                }
            )
            return redirect('appointments:detail', pk=appointment.pk)

        # Form invalid, re-render
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)

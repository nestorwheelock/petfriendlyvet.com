"""Forms for appointment management."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.locations.models import Location
from apps.pets.models import Pet

from .models import Appointment, ServiceType


class StaffAppointmentForm(forms.ModelForm):
    """Form for staff to create/edit appointments."""

    scheduled_date = forms.DateField(
        label=_('Date'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input rounded-md border-gray-300 shadow-sm'
        })
    )
    scheduled_time = forms.TimeField(
        label=_('Time'),
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-input rounded-md border-gray-300 shadow-sm'
        })
    )

    class Meta:
        model = Appointment
        fields = [
            'owner', 'pet', 'service', 'location', 'veterinarian',
            'scheduled_date', 'scheduled_time', 'status', 'notes'
        ]
        widgets = {
            'owner': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm'
            }),
            'pet': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm'
            }),
            'service': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm'
            }),
            'location': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm'
            }),
            'veterinarian': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea rounded-md border-gray-300 shadow-sm',
                'rows': 3,
                'placeholder': _('Notes about the appointment...')
            }),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')

        # Pre-populate date/time from instance BEFORE super().__init__
        # This ensures the values appear in the form widgets
        if instance and instance.pk and instance.scheduled_start:
            initial = kwargs.setdefault('initial', {})
            initial.setdefault('scheduled_date', instance.scheduled_start.date())
            initial.setdefault('scheduled_time', instance.scheduled_start.time())

        super().__init__(*args, **kwargs)

        # Filter querysets
        self.fields['owner'].queryset = User.objects.filter(is_active=True)
        self.fields['pet'].queryset = Pet.objects.filter(is_archived=False)
        self.fields['service'].queryset = ServiceType.objects.filter(is_active=True)
        self.fields['location'].queryset = Location.objects.filter(is_active=True)
        self.fields['veterinarian'].queryset = User.objects.filter(is_staff=True, is_active=True)
        self.fields['veterinarian'].required = False
        self.fields['location'].required = False
        self.fields['status'].required = False  # Default to 'scheduled' for new appointments

    def clean(self):
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')
        service = cleaned_data.get('service')

        if scheduled_date and scheduled_time:
            from django.utils import timezone
            from datetime import datetime, timedelta

            # Combine date and time
            naive_dt = datetime.combine(scheduled_date, scheduled_time)
            scheduled_start = timezone.make_aware(naive_dt)
            cleaned_data['scheduled_start'] = scheduled_start

            # Calculate end time based on service duration
            if service:
                duration = timedelta(minutes=service.duration_minutes)
                cleaned_data['scheduled_end'] = scheduled_start + duration

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.scheduled_start = self.cleaned_data['scheduled_start']
        instance.scheduled_end = self.cleaned_data['scheduled_end']
        # Set default status for new appointments
        if not instance.pk and not instance.status:
            instance.status = 'scheduled'
        if commit:
            instance.save()
        return instance

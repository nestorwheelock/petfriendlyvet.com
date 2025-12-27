"""EMR forms."""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User

from .models import Encounter


class EncounterEditForm(forms.ModelForm):
    """Form for editing encounter details (not state transitions)."""

    class Meta:
        model = Encounter
        fields = [
            'encounter_type',
            'chief_complaint',
            'assigned_vet',
            'assigned_tech',
            'room',
        ]
        widgets = {
            'encounter_type': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm w-full'
            }),
            'chief_complaint': forms.Textarea(attrs={
                'class': 'form-textarea rounded-md border-gray-300 shadow-sm w-full',
                'rows': 3,
                'placeholder': _('Reason for visit...')
            }),
            'assigned_vet': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm w-full'
            }),
            'assigned_tech': forms.Select(attrs={
                'class': 'form-select rounded-md border-gray-300 shadow-sm w-full'
            }),
            'room': forms.TextInput(attrs={
                'class': 'form-input rounded-md border-gray-300 shadow-sm w-full',
                'placeholder': _('e.g., Exam 1, Surgery')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active staff for vet/tech assignment
        self.fields['assigned_vet'].queryset = User.objects.filter(
            is_staff=True, is_active=True
        )
        self.fields['assigned_tech'].queryset = User.objects.filter(
            is_staff=True, is_active=True
        )
        self.fields['assigned_vet'].required = False
        self.fields['assigned_tech'].required = False

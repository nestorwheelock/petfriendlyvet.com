"""Forms for locations management."""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import ExamRoom


class ExamRoomForm(forms.ModelForm):
    """Form for creating/editing exam rooms."""

    class Meta:
        model = ExamRoom
        fields = ['name', 'room_type', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': _('e.g., Room 1, Exam A, Surgery'),
            }),
            'room_type': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox',
            }),
        }

    def __init__(self, *args, location=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = location

    def clean_name(self):
        name = self.cleaned_data['name']
        if self.location:
            qs = ExamRoom.objects.filter(location=self.location, name=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    _('A room with this name already exists at this location.')
                )
        return name

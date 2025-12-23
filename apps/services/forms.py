"""Forms for external services."""
from django import forms

from apps.pets.models import Pet
from .models import Referral


class ReferralForm(forms.ModelForm):
    """Form for creating a referral."""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Only show user's pets
            self.fields['pet'].queryset = Pet.objects.filter(owner=user)

    class Meta:
        model = Referral
        fields = ['pet', 'preferred_date', 'notes']
        widgets = {
            'pet': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'rows': 3,
                'placeholder': 'Any special requirements or notes...'
            }),
        }

"""Forms for travel certificates."""
from django import forms

from apps.pets.models import Pet
from .models import HealthCertificate, TravelPlan, TravelDestination


class CertificateRequestForm(forms.ModelForm):
    """Form for requesting a health certificate."""

    def __init__(self, *args, pet=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pet = pet
        self.fields['destination'].queryset = TravelDestination.objects.filter(
            is_active=True
        ).order_by('country_name')

    class Meta:
        model = HealthCertificate
        fields = ['destination', 'travel_date', 'notes']
        widgets = {
            'destination': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'travel_date': forms.DateInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'rows': 3,
                'placeholder': 'Any special requirements or notes...'
            }),
        }


class TravelPlanForm(forms.ModelForm):
    """Form for creating a travel plan."""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['pet'].queryset = Pet.objects.filter(owner=user)
        self.fields['destination'].queryset = TravelDestination.objects.filter(
            is_active=True
        ).order_by('country_name')

    class Meta:
        model = TravelPlan
        fields = ['pet', 'destination', 'departure_date', 'return_date', 'airline', 'flight_number', 'notes']
        widgets = {
            'pet': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'destination': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'departure_date': forms.DateInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'return_date': forms.DateInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'airline': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'e.g., American Airlines'
            }),
            'flight_number': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'e.g., AA123'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'rows': 3,
            }),
        }

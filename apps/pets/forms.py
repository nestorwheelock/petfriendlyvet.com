"""Forms for pets management."""
from django import forms
from django.forms.widgets import ClearableFileInput

from .models import Pet, PetDocument


class StyledClearableFileInput(ClearableFileInput):
    """Clearable file input with Tailwind styling."""

    template_name = 'widgets/clearable_file_input.html'


class PetForm(forms.ModelForm):
    """Form for creating and editing pets."""

    class Meta:
        model = Pet
        fields = [
            'name',
            'species',
            'breed',
            'gender',
            'date_of_birth',
            'weight_kg',
            'microchip_id',
            'is_neutered',
            'photo',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Pet name'
            }),
            'species': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'breed': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Breed (optional)'
            }),
            'gender': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'type': 'date'
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Weight in kg',
                'step': '0.1'
            }),
            'microchip_id': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Microchip ID (optional)'
            }),
            'is_neutered': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded'
            }),
            'photo': StyledClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100',
                'accept': 'image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
        }


class PetDocumentForm(forms.ModelForm):
    """Form for uploading pet documents."""

    class Meta:
        model = PetDocument
        fields = [
            'title',
            'document_type',
            'description',
            'file',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'placeholder': 'Document title'
            }),
            'document_type': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500',
                'rows': 3,
                'placeholder': 'Description (optional)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100'
            }),
        }

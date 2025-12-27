"""Forms for practice app staff management."""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import StaffProfile, Shift, Task, TimeEntry

User = get_user_model()


class StaffCreateForm(forms.Form):
    """Combined form to create User + StaffProfile together.

    Supports two scenarios:
    1. New user: Creates User + StaffProfile (password required)
    2. Existing user without StaffProfile: Links existing User to new StaffProfile
    """

    # User fields
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'input input-bordered w-full'})
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'})
    )
    password1 = forms.CharField(
        label='Password',
        required=False,  # Not required for existing users
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        required=False,  # Not required for existing users
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'})
    )

    # StaffProfile fields
    role = forms.ChoiceField(
        choices=StaffProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'})
    )
    title = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'})
    )
    emergency_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'})
    )
    hire_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input input-bordered w-full'
        })
    )
    dea_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'})
    )
    dea_expiration = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input input-bordered w-full'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.existing_user = None  # Will be set if email matches existing user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            existing_user = User.objects.get(email=email)
            # Check if user already has a StaffProfile
            if hasattr(existing_user, 'staff_profile'):
                raise ValidationError('This user already has a staff profile.')
            # Store the existing user for use in save()
            self.existing_user = existing_user
        except User.DoesNotExist:
            # New user - will create in save()
            self.existing_user = None
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Only require passwords for new users
        if self.existing_user is None:
            if not password1:
                self.add_error('password1', 'Password is required for new users.')
            if not password2:
                self.add_error('password2', 'Password confirmation is required for new users.')
            elif password1 and password2 and password1 != password2:
                raise ValidationError('Passwords do not match.')
        else:
            # For existing users, passwords are ignored
            pass

        return cleaned_data

    def save(self):
        """Create User (if needed) and StaffProfile."""
        if self.existing_user:
            # Use existing user, just update their staff status and name if needed
            user = self.existing_user
            user.is_staff = True
            user.role = 'staff'
            # Update name if provided
            if self.cleaned_data.get('first_name'):
                user.first_name = self.cleaned_data['first_name']
            if self.cleaned_data.get('last_name'):
                user.last_name = self.cleaned_data['last_name']
            user.save()
        else:
            # Create new user
            email = self.cleaned_data['email']
            username = email.split('@')[0]

            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Create User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=self.cleaned_data['password1'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                is_staff=True,
                role='staff',
            )

        # Create StaffProfile
        profile = StaffProfile.objects.create(
            user=user,
            role=self.cleaned_data['role'],
            title=self.cleaned_data.get('title', ''),
            phone=self.cleaned_data.get('phone', ''),
            emergency_phone=self.cleaned_data.get('emergency_phone', ''),
            hire_date=self.cleaned_data.get('hire_date'),
            dea_number=self.cleaned_data.get('dea_number', ''),
            dea_expiration=self.cleaned_data.get('dea_expiration'),
        )

        return profile


class StaffEditForm(forms.ModelForm):
    """Form to edit StaffProfile fields (not password)."""

    class Meta:
        model = StaffProfile
        fields = [
            'role', 'title', 'phone', 'emergency_phone',
            'hire_date', 'dea_number', 'dea_expiration',
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'title': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'hire_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered w-full'
            }),
            'dea_number': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'dea_expiration': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered w-full'
            }),
        }


class ShiftForm(forms.ModelForm):
    """Form for creating/editing shifts."""

    class Meta:
        model = Shift
        fields = ['staff', 'date', 'start_time', 'end_time', 'notes']
        widgets = {
            'staff': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered w-full'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'input input-bordered w-full'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'input input-bordered w-full'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and end_time <= start_time:
            raise ValidationError('End time must be after start time.')

        return cleaned_data


class TaskForm(forms.ModelForm):
    """Form for creating/editing tasks."""

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'priority', 'status',
            'due_date', 'assigned_to', 'pet', 'appointment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4
            }),
            'priority': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'status': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'input input-bordered w-full'
            }),
            'assigned_to': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'pet': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'appointment': forms.Select(attrs={'class': 'select select-bordered w-full'}),
        }


class TimeEntryForm(forms.ModelForm):
    """Form for editing time entries."""

    class Meta:
        model = TimeEntry
        fields = ['clock_in', 'clock_out', 'break_minutes', 'notes']
        widgets = {
            'clock_in': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'input input-bordered w-full'
            }),
            'clock_out': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'input input-bordered w-full'
            }),
            'break_minutes': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3
            }),
        }

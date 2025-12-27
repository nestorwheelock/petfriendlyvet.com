"""Forms for superadmin management."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Role
from apps.practice.models import ClinicSettings

User = get_user_model()


class RoleForm(forms.ModelForm):
    """Form for creating and editing roles."""

    class Meta:
        model = Role
        fields = ['name', 'slug', 'description', 'hierarchy_level', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., Practice Manager',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'e.g., practice-manager',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Description of this role...',
            }),
            'hierarchy_level': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 10,
                'max': 99,
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary',
            }),
        }

    def save(self, commit=True):
        """Create/update role and linked Django Group."""
        role = super().save(commit=False)

        # Create or update the linked Group
        if role.pk:
            # Updating existing role - update group name if changed
            if role.group and role.group.name != role.name:
                role.group.name = role.name
                role.group.save()
        else:
            # Creating new role - create group first
            group, _ = Group.objects.get_or_create(name=role.name)
            role.group = group

        if commit:
            role.save()

        return role


class UserForm(forms.ModelForm):
    """Form for creating and editing users."""

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'user@example.com',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Last name',
            }),
            'role': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-primary',
            }),
            'is_superuser': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-error',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox checkbox-success',
            }),
        }


class UserCreateForm(UserForm):
    """Form for creating new users with password."""

    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Password',
        }),
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirm password',
        }),
    )

    class Meta(UserForm.Meta):
        fields = ['email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser', 'is_active']

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords don't match."))
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ClinicSettingsForm(forms.ModelForm):
    """Form for editing clinic settings."""

    class Meta:
        model = ClinicSettings
        fields = [
            'name', 'legal_name', 'tax_id',
            'address', 'phone', 'email', 'website',
            'opening_time', 'closing_time', 'days_open',
            'emergency_phone', 'emergency_available',
            'facebook_url', 'instagram_url', 'google_maps_url',
            'logo', 'primary_color',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'legal_name': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'tax_id': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'address': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full bg-base-200 text-base-content', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'website': forms.URLInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'emergency_available': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
            'opening_time': forms.TimeInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content', 'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content', 'type': 'time'}),
            'days_open': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content', 'placeholder': 'e.g., Mon-Fri'}),
            'facebook_url': forms.URLInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'instagram_url': forms.URLInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'google_maps_url': forms.URLInput(attrs={'class': 'input input-bordered w-full bg-base-200 text-base-content'}),
            'primary_color': forms.TextInput(attrs={'class': 'input input-bordered w-full bg-base-200', 'type': 'color'}),
        }

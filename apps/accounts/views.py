"""Account views."""
import hashlib
import secrets
from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth import views as auth_views, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView, TemplateView, FormView

from .models import User, EmailChangeRequest


class RegistrationForm(forms.ModelForm):
    """User registration form."""

    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '••••••••'
        })
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '••••••••'
        })
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'placeholder': 'tu@email.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'placeholder': 'Juan'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'placeholder': 'García'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'placeholder': '+52 55 1234 5678'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('This email is already registered.'))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Passwords do not match.'))

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    """User profile edit form."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'preferred_language', 'marketing_consent']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
            }),
            'marketing_consent': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-500 border-gray-300 rounded'
            }),
        }


class PasswordResetRequestForm(forms.Form):
    """Password reset request form."""

    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'tu@email.com'
        })
    )


class SetNewPasswordForm(forms.Form):
    """Set new password form."""

    password1 = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '••••••••'
        })
    )
    password2 = forms.CharField(
        label=_('Confirm New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '••••••••'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Passwords do not match.'))

        return cleaned_data


class LoginView(auth_views.LoginView):
    """Custom login view."""

    template_name = 'accounts/login.html'


class LogoutView(auth_views.LogoutView):
    """Custom logout view.

    Allows GET requests for logout (Django 4.1+ defaults to POST-only).
    This is safe for this app since it's internal/authenticated.
    """

    http_method_names = ['get', 'post', 'options']

    def get(self, request, *args, **kwargs):
        """Handle GET request same as POST."""
        return self.post(request, *args, **kwargs)


class RegisterView(CreateView):
    """User registration view."""

    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, _('Welcome! Your account has been created.'))
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view - requires authentication."""

    template_name = 'accounts/profile.html'


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile."""

    template_name = 'accounts/profile_edit.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, _('Your profile has been updated.'))
        return super().form_valid(form)


class ChangePasswordView(LoginRequiredMixin, FormView):
    """Change password view."""

    template_name = 'accounts/change_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('accounts:profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, _('Your password has been changed.'))
        return super().form_valid(form)


class PasswordResetRequestView(FormView):
    """Request password reset email."""

    template_name = 'accounts/password_reset.html'
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy('accounts:password_reset_sent')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = self.request.build_absolute_uri(
                reverse_lazy('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            send_mail(
                subject=_('Password Reset - Pet-Friendly Vet'),
                message=f'Click this link to reset your password: {reset_url}',
                from_email=None,
                recipient_list=[email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass
        return super().form_valid(form)


class PasswordResetSentView(TemplateView):
    """Password reset email sent confirmation."""

    template_name = 'accounts/password_reset_sent.html'


class PasswordResetConfirmView(FormView):
    """Confirm password reset with new password."""

    template_name = 'accounts/password_reset_confirm.html'
    form_class = SetNewPasswordForm
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        self.user = self.get_user(kwargs.get('uidb64'))
        self.valid_link = self.user is not None and default_token_generator.check_token(
            self.user, kwargs.get('token')
        )
        if not self.valid_link:
            return redirect('accounts:password_reset_invalid')
        return super().dispatch(request, *args, **kwargs)

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None

    def form_valid(self, form):
        self.user.set_password(form.cleaned_data['password1'])
        self.user.save()
        messages.success(self.request, _('Your password has been reset. Please login.'))
        return super().form_valid(form)


class PasswordResetInvalidView(TemplateView):
    """Invalid password reset link."""

    template_name = 'accounts/password_reset_invalid.html'


class DeleteAccountView(LoginRequiredMixin, TemplateView):
    """Account deletion confirmation - soft deletes by deactivating."""

    template_name = 'accounts/delete_account.html'

    def post(self, request, *args, **kwargs):
        user = request.user
        user.is_active = False
        user.save()
        messages.info(request, _('Your account has been deactivated.'))
        return redirect('accounts:login')


class EmailChangeForm(forms.Form):
    """Form to request email address change."""

    new_email = forms.EmailField(
        label=_('New Email Address'),
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'nuevo@email.com'
        })
    )
    password = forms.CharField(
        label=_('Current Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '••••••••'
        }),
        help_text=_('Enter your current password to confirm this change.')
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email')
        if new_email and User.objects.filter(email=new_email).exists():
            raise forms.ValidationError(_('This email address is already in use.'))
        if new_email == self.user.email:
            raise forms.ValidationError(_('This is already your email address.'))
        return new_email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and not self.user.check_password(password):
            raise forms.ValidationError(_('Incorrect password.'))
        return password


class EmailChangeRequestView(LoginRequiredMixin, FormView):
    """Request to change email address."""

    template_name = 'accounts/email_change.html'
    form_class = EmailChangeForm
    success_url = reverse_lazy('accounts:email_change_sent')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        new_email = form.cleaned_data['new_email']

        EmailChangeRequest.objects.filter(user=user, confirmed_at__isnull=True).delete()

        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)

        email_change = EmailChangeRequest.objects.create(
            user=user,
            new_email=new_email,
            old_email=user.email or '',
            token=token,
            expires_at=expires_at
        )

        confirm_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:email_change_confirm', kwargs={'token': token})
        )

        send_mail(
            subject=_('Confirm Email Change - Pet-Friendly Vet'),
            message=_(
                'You have requested to change your email address.\n\n'
                'Click this link to confirm your new email address: %(url)s\n\n'
                'This link will expire in 24 hours.\n\n'
                'If you did not request this change, please ignore this email.'
            ) % {'url': confirm_url},
            from_email=None,
            recipient_list=[new_email],
            fail_silently=True,
        )

        if user.email:
            send_mail(
                subject=_('Email Change Requested - Pet-Friendly Vet'),
                message=_(
                    'An email change has been requested for your account.\n\n'
                    'Your email will be changed to: %(new_email)s\n\n'
                    'If you did not request this change, please contact us immediately.'
                ) % {'new_email': new_email},
                from_email=None,
                recipient_list=[user.email],
                fail_silently=True,
            )

        return super().form_valid(form)


class EmailChangeSentView(LoginRequiredMixin, TemplateView):
    """Email change verification sent confirmation."""

    template_name = 'accounts/email_change_sent.html'


class EmailChangeConfirmView(TemplateView):
    """Confirm email change with token."""

    template_name = 'accounts/email_change_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = self.kwargs.get('token')

        try:
            email_change = EmailChangeRequest.objects.get(token=token)
            context['email_change'] = email_change
            context['valid'] = email_change.is_valid
            context['expired'] = email_change.is_expired
            context['already_confirmed'] = email_change.confirmed_at is not None
        except EmailChangeRequest.DoesNotExist:
            context['valid'] = False
            context['not_found'] = True

        return context

    def post(self, request, *args, **kwargs):
        token = self.kwargs.get('token')

        try:
            email_change = EmailChangeRequest.objects.get(token=token)

            if not email_change.is_valid:
                if email_change.is_expired:
                    messages.error(request, _('This link has expired. Please request a new email change.'))
                else:
                    messages.error(request, _('This email change has already been confirmed.'))
                return redirect('accounts:profile')

            user = email_change.user
            old_email = user.email
            user.email = email_change.new_email
            user.username = email_change.new_email
            user.email_verified = True
            user.save(update_fields=['email', 'username', 'email_verified'])

            email_change.confirmed_at = timezone.now()
            email_change.save(update_fields=['confirmed_at'])

            messages.success(
                request,
                _('Your email has been changed from %(old)s to %(new)s.') % {
                    'old': old_email or _('(none)'),
                    'new': email_change.new_email
                }
            )
            return redirect('accounts:profile')

        except EmailChangeRequest.DoesNotExist:
            messages.error(request, _('Invalid email change link.'))
            return redirect('accounts:profile')

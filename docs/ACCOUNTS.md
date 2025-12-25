# Accounts Module

The `apps.accounts` module handles user authentication, registration, profile management, password reset, and role-based access control for the Pet-Friendly Vet application.

## Table of Contents

- [Overview](#overview)
- [Models](#models)
  - [User](#user)
- [Validators](#validators)
- [Forms](#forms)
- [Views](#views)
- [URL Patterns](#url-patterns)
- [Workflows](#workflows)
  - [User Registration](#user-registration)
  - [Login/Logout](#loginlogout)
  - [Profile Management](#profile-management)
  - [Password Reset](#password-reset)
  - [Account Deletion](#account-deletion)
- [User Roles](#user-roles)
- [Security Features](#security-features)
- [Integration Points](#integration-points)
- [Query Examples](#query-examples)
- [Testing](#testing)

## Overview

The accounts module provides core authentication functionality:

- **Custom User Model** - Extended Django user with roles and preferences
- **Multi-language Support** - Spanish, English, German, French, Italian
- **Multiple Auth Methods** - Email, phone, or Google OAuth
- **Role-Based Access** - Pet owner, staff, veterinarian, administrator
- **Secure File Uploads** - Validated avatar images

```
┌─────────────────────────────────────────────────────────────┐
│                   AUTHENTICATION FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌────────────┐  │
│   │   Register   │────>│    Login     │────>│   Profile  │  │
│   │  (new user)  │     │  (existing)  │     │  (manage)  │  │
│   └──────────────┘     └──────────────┘     └────────────┘  │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                    User Roles                         │  │
│   ├──────────────┬──────────────┬──────────────┬─────────┤  │
│   │  Pet Owner   │    Staff     │ Veterinarian │  Admin  │  │
│   │  (default)   │              │              │         │  │
│   └──────────────┴──────────────┴──────────────┴─────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Models

### User

Location: `apps/accounts/models.py`

Custom user model extending Django's AbstractUser.

```python
class User(AbstractUser):
    """Custom user model for Pet-Friendly Vet."""

    AUTH_METHOD_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('google', 'Google'),
    ]

    ROLE_CHOICES = [
        ('owner', 'Pet Owner'),
        ('staff', 'Staff'),
        ('vet', 'Veterinarian'),
        ('admin', 'Administrator'),
    ]

    # Contact info
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    # Preferences
    preferred_language = models.CharField(
        max_length=5,
        default='es',
        choices=[
            ('es', 'Español'),
            ('en', 'English'),
            ('de', 'Deutsch'),
            ('fr', 'Français'),
            ('it', 'Italiano'),
        ]
    )

    # Authentication
    auth_method = models.CharField(max_length=20, choices=AUTH_METHOD_CHOICES, default='email')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='owner')

    # Profile picture (with security validators)
    avatar = models.ImageField(
        upload_to=avatar_upload_path,
        validators=[validate_file_size, validate_image_type],
        null=True,
        blank=True
    )

    # Consent tracking
    marketing_consent = models.BooleanField(default=False)
    marketing_consent_date = models.DateTimeField(null=True, blank=True)

    # Helper properties
    @property
    def is_pet_owner(self):
        return self.role == 'owner'

    @property
    def is_staff_member(self):
        return self.role in ['staff', 'vet', 'admin']

    @property
    def is_veterinarian(self):
        return self.role == 'vet'
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `email` | EmailField | Unique email address (optional) |
| `phone_number` | CharField | Unique phone number (optional) |
| `phone_verified` | Boolean | Phone verification status |
| `email_verified` | Boolean | Email verification status |
| `preferred_language` | CharField | UI language preference |
| `auth_method` | CharField | How user authenticates |
| `role` | CharField | User role for permissions |
| `avatar` | ImageField | Profile picture with validation |
| `marketing_consent` | Boolean | Marketing email consent |

## Validators

Location: `apps/accounts/validators.py`

Secure file upload validation for avatar images.

### validate_file_size

```python
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

def validate_file_size(file):
    """Validate that uploaded file is under the size limit."""
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(
            'File size must be no more than 2 MB. Your file is %(size)s.',
            params={'size': f'{file.size / (1024 * 1024):.1f} MB'},
            code='file_too_large'
        )
```

### validate_image_type

```python
ALLOWED_IMAGE_TYPES = ['JPEG', 'PNG', 'GIF', 'WEBP']

def validate_image_type(file):
    """Validate that uploaded file is a valid image type.

    Uses Pillow to verify file content, not just extension or MIME type.
    This prevents attackers from uploading malicious files with renamed extensions.
    """
    file.seek(0)
    try:
        img = Image.open(file)
        img.verify()
        if img.format not in ALLOWED_IMAGE_TYPES:
            raise ValidationError('Unsupported image type.')
    except (IOError, SyntaxError):
        raise ValidationError('Invalid image file.')
    finally:
        file.seek(0)
```

### sanitize_filename

```python
def sanitize_filename(filename):
    """Sanitize uploaded filename to prevent directory traversal."""
    # Remove path components
    filename = os.path.basename(filename)
    # Remove directory traversal attempts
    filename = filename.replace('..', '')
    # Keep only alphanumeric, hyphen, underscore
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return f"{name}{ext}"
```

### avatar_upload_path

```python
def avatar_upload_path(instance, filename):
    """Generate secure upload path for avatar images."""
    safe_name = sanitize_filename(filename)
    return f'avatars/user_{instance.pk}/{safe_name}'
```

## Forms

Location: `apps/accounts/views.py`

### RegistrationForm

```python
class RegistrationForm(forms.ModelForm):
    """User registration form."""

    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean(self):
        # Validate passwords match
        if password1 != password2:
            raise forms.ValidationError('Passwords do not match.')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
```

### ProfileEditForm

```python
class ProfileEditForm(forms.ModelForm):
    """User profile edit form."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'preferred_language', 'marketing_consent']
```

### PasswordResetRequestForm

```python
class PasswordResetRequestForm(forms.Form):
    """Password reset request form."""
    email = forms.EmailField()
```

### SetNewPasswordForm

```python
class SetNewPasswordForm(forms.Form):
    """Set new password form."""
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        # Validate passwords match
```

## Views

Location: `apps/accounts/views.py`

### LoginView

Standard Django login view with custom template.

```python
class LoginView(auth_views.LoginView):
    """Custom login view."""
    template_name = 'accounts/login.html'
```

### LogoutView

Standard Django logout view.

```python
class LogoutView(auth_views.LogoutView):
    """Custom logout view."""
    pass
```

### RegisterView

User registration with automatic login after success.

```python
class RegisterView(CreateView):
    """User registration view."""
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  # Auto-login
        messages.success(self.request, 'Welcome! Your account has been created.')
        return response
```

### ProfileView

View user profile (read-only).

```python
class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view - requires authentication."""
    template_name = 'accounts/profile.html'
```

### ProfileEditView

Edit user profile details.

```python
class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile."""
    template_name = 'accounts/profile_edit.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user
```

### ChangePasswordView

Change password while logged in.

```python
class ChangePasswordView(LoginRequiredMixin, FormView):
    """Change password view."""
    template_name = 'accounts/change_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)  # Keep user logged in
        messages.success(self.request, 'Your password has been changed.')
        return super().form_valid(form)
```

### PasswordResetRequestView

Request password reset email.

```python
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
                subject='Password Reset - Pet-Friendly Vet',
                message=f'Click this link to reset your password: {reset_url}',
                from_email=None,
                recipient_list=[email],
            )
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        return super().form_valid(form)
```

### PasswordResetConfirmView

Confirm password reset with new password.

```python
class PasswordResetConfirmView(FormView):
    """Confirm password reset with new password."""
    template_name = 'accounts/password_reset_confirm.html'
    form_class = SetNewPasswordForm
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        self.user = self.get_user(kwargs.get('uidb64'))
        self.valid_link = self.user and default_token_generator.check_token(
            self.user, kwargs.get('token')
        )
        if not self.valid_link:
            return redirect('accounts:password_reset_invalid')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.user.set_password(form.cleaned_data['password1'])
        self.user.save()
        messages.success(self.request, 'Your password has been reset. Please login.')
        return super().form_valid(form)
```

### DeleteAccountView

Soft-delete account by deactivation.

```python
class DeleteAccountView(LoginRequiredMixin, TemplateView):
    """Account deletion confirmation - soft deletes by deactivating."""
    template_name = 'accounts/delete_account.html'

    def post(self, request, *args, **kwargs):
        user = request.user
        user.is_active = False
        user.save()
        messages.info(request, 'Your account has been deactivated.')
        return redirect('accounts:login')
```

## URL Patterns

Location: `apps/accounts/urls.py`

```python
app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('profile/delete/', views.DeleteAccountView.as_view(), name='delete_account'),

    # Password reset
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/sent/', views.PasswordResetSentView.as_view(), name='password_reset_sent'),
    path('password-reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/invalid/', views.PasswordResetInvalidView.as_view(), name='password_reset_invalid'),
]
```

## Workflows

### User Registration

```python
from apps.accounts.models import User

# User registers via form
user = User.objects.create(
    email='user@example.com',
    username='user@example.com',
    first_name='Juan',
    last_name='García',
    phone_number='+52 55 1234 5678',
    role='owner',  # Default
    preferred_language='es',  # Default
)
user.set_password('secure_password')
user.save()

# User is automatically logged in after registration
```

### Login/Logout

```python
from django.contrib.auth import authenticate, login, logout

# Login
user = authenticate(request, username='user@example.com', password='password')
if user is not None:
    login(request, user)

# Logout
logout(request)
```

### Profile Management

```python
from apps.accounts.models import User

# Update profile
user = request.user
user.first_name = 'Updated Name'
user.preferred_language = 'en'
user.marketing_consent = True
user.save()

# Upload avatar
user.avatar = uploaded_file  # Validators run automatically
user.save()
```

### Password Reset

```python
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

# Generate reset token
user = User.objects.get(email='user@example.com')
token = default_token_generator.make_token(user)
uid = urlsafe_base64_encode(force_bytes(user.pk))

# Verify token
from django.utils.http import urlsafe_base64_decode
uid = urlsafe_base64_decode(uidb64).decode()
user = User.objects.get(pk=uid)
is_valid = default_token_generator.check_token(user, token)

# Set new password
user.set_password('new_password')
user.save()
```

### Account Deletion

```python
# Soft delete (deactivate)
user = request.user
user.is_active = False
user.save()

# User can no longer login
# Data is preserved for potential reactivation
```

## User Roles

| Role | Code | Description | Permissions |
|------|------|-------------|-------------|
| Pet Owner | `owner` | Default role for customers | Manage pets, book appointments |
| Staff | `staff` | Clinic staff members | Access staff dashboard |
| Veterinarian | `vet` | Licensed veterinarians | Medical records, prescriptions |
| Administrator | `admin` | System administrators | Full system access |

### Role-Based Access Examples

```python
from apps.accounts.models import User

user = User.objects.get(pk=user_id)

# Check role
if user.is_pet_owner:
    # Show customer dashboard
    pass

if user.is_staff_member:
    # Show staff dashboard
    pass

if user.is_veterinarian:
    # Show medical tools
    pass

# In views
from django.contrib.auth.mixins import UserPassesTestMixin

class StaffOnlyView(UserPassesTestMixin, TemplateView):
    def test_func(self):
        return self.request.user.is_staff_member

class VetOnlyView(UserPassesTestMixin, TemplateView):
    def test_func(self):
        return self.request.user.is_veterinarian
```

## Security Features

### Avatar Upload Security

1. **File Size Limit** - Max 2 MB
2. **Content Validation** - Pillow verifies actual image format
3. **Type Whitelist** - Only JPEG, PNG, GIF, WebP
4. **Filename Sanitization** - Prevents directory traversal
5. **Unique Paths** - Files stored in user-specific directories

### Password Security

- Django's built-in password hashing (PBKDF2)
- Password confirmation on registration
- Secure token-based password reset
- Session preserved after password change

### Account Protection

- Unique email constraint
- Unique phone number constraint
- Soft-delete prevents data loss
- Token expiration for password reset

## Integration Points

### With Pets Module

```python
from apps.accounts.models import User
from apps.pets.models import Pet

# Get user's pets
user = User.objects.get(pk=user_id)
pets = Pet.objects.filter(owner=user)

# Verify ownership
def can_access_pet(user, pet):
    return pet.owner == user or user.is_staff_member
```

### With Appointments Module

```python
from apps.accounts.models import User
from apps.appointments.models import Appointment

# Get user's appointments
appointments = Appointment.objects.filter(owner=user)

# Staff can see all appointments
if user.is_staff_member:
    appointments = Appointment.objects.all()
```

### With Notifications Module

```python
from apps.accounts.models import User
from apps.notifications.models import NotificationPreference

# Create default preferences for new user
def on_user_created(user):
    NotificationPreference.objects.create(user=user)
```

### With CRM Module

```python
from apps.accounts.models import User
from apps.crm.models import OwnerProfile

# Link CRM profile to user
profile = OwnerProfile.objects.create(
    user=user,
    preferred_contact='email',
    notes='New customer from website registration',
)
```

## Query Examples

### User Queries

```python
from apps.accounts.models import User
from django.db.models import Count, Q

# Active users
active = User.objects.filter(is_active=True)

# Users by role
vets = User.objects.filter(role='vet')
staff = User.objects.filter(role__in=['staff', 'vet', 'admin'])

# Users by language
spanish_users = User.objects.filter(preferred_language='es')

# Users who consented to marketing
marketable = User.objects.filter(
    marketing_consent=True,
    email__isnull=False
)

# Search users
query = 'garcía'
results = User.objects.filter(
    Q(first_name__icontains=query) |
    Q(last_name__icontains=query) |
    Q(email__icontains=query)
)

# Users with verified contact
verified = User.objects.filter(
    Q(email_verified=True) | Q(phone_verified=True)
)

# Users by auth method
google_users = User.objects.filter(auth_method='google')
```

### Registration Statistics

```python
from apps.accounts.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth

# Registrations per day
daily = User.objects.annotate(
    date=TruncDate('date_joined')
).values('date').annotate(
    count=Count('id')
).order_by('-date')[:30]

# Registrations per month
monthly = User.objects.annotate(
    month=TruncMonth('date_joined')
).values('month').annotate(
    count=Count('id')
).order_by('-month')[:12]

# Role distribution
role_stats = User.objects.values('role').annotate(
    count=Count('id')
).order_by('-count')

# Language distribution
lang_stats = User.objects.values('preferred_language').annotate(
    count=Count('id')
).order_by('-count')
```

### Account Management Queries

```python
from apps.accounts.models import User
from datetime import timedelta
from django.utils import timezone

# Inactive accounts (not logged in for 90 days)
inactive = User.objects.filter(
    last_login__lt=timezone.now() - timedelta(days=90)
)

# Accounts created but never logged in
never_logged_in = User.objects.filter(last_login__isnull=True)

# Deactivated accounts
deactivated = User.objects.filter(is_active=False)

# Recent registrations
recent = User.objects.filter(
    date_joined__gte=timezone.now() - timedelta(days=7)
).order_by('-date_joined')
```

## Testing

### Unit Tests

Location: `tests/test_accounts.py`

```bash
# Run accounts unit tests
python -m pytest tests/test_accounts.py -v
```

### Browser Tests

Location: `tests/e2e/browser/test_accounts.py`

```bash
# Run accounts browser tests
python -m pytest tests/e2e/browser/test_accounts.py -v

# Run with visible browser
python -m pytest tests/e2e/browser/test_accounts.py -v --headed --slowmo=500
```

### Key Test Scenarios

1. **Registration**
   - Register with valid data
   - Reject duplicate email
   - Validate password match
   - Auto-login after registration

2. **Login/Logout**
   - Login with valid credentials
   - Reject invalid credentials
   - Logout clears session

3. **Profile Management**
   - View profile
   - Edit profile details
   - Change password
   - Upload avatar (with validation)

4. **Password Reset**
   - Request reset email
   - Valid token works
   - Invalid/expired token rejected
   - New password is set

5. **File Upload Security**
   - Reject oversized files
   - Reject non-image files
   - Accept valid images
   - Sanitize filenames

6. **Account Deletion**
   - Soft-delete deactivates
   - User cannot login after
   - Data is preserved

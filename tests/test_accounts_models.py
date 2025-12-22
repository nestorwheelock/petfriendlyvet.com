"""Tests for accounts app models."""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests for the custom User model."""

    def test_create_user(self):
        """Should be able to create a user with email."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
        )
        assert user.email == 'test@example.com'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_superuser(self):
        """Should be able to create a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword123',
        )
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_user_phone_number_field(self):
        """User should have a phone_number field."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            phone_number='+529981234567',
        )
        assert user.phone_number == '+529981234567'

    def test_user_role_field(self):
        """User should have a role field with default value."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
        )
        assert user.role == 'owner'

    def test_user_auth_method_field(self):
        """User should have an auth_method field with default value."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
        )
        assert user.auth_method == 'email'

    def test_user_string_representation(self):
        """User string representation should be email or username."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
        )
        assert str(user) in ['test@example.com', 'testuser']

    def test_user_role_choices(self):
        """User role should accept valid choices."""
        valid_roles = ['owner', 'staff', 'admin']
        for role in valid_roles:
            user = User(
                username=f'testuser_{role}',
                email=f'{role}@example.com',
                role=role,
            )
            user.set_password('testpassword123')
            user.full_clean()

    def test_user_auth_method_choices(self):
        """User auth_method should accept valid choices."""
        valid_methods = ['email', 'google', 'phone']
        for method in valid_methods:
            user = User(
                username=f'testuser_{method}',
                email=f'{method}@example.com',
                auth_method=method,
            )
            user.set_password('testpassword123')
            user.full_clean()

"""Pytest configuration for Pet-Friendly Vet tests."""
import os

import pytest


@pytest.fixture
def user_factory(db):
    """Factory for creating test users."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    def create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123',
        **kwargs
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs
        )

    return create_user


@pytest.fixture
def authenticated_client(client, user_factory):
    """Return a Django test client with an authenticated user."""
    user = user_factory()
    client.force_login(user)
    return client

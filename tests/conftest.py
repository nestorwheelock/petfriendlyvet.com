"""Pytest configuration for Pet-Friendly Vet tests."""
import asyncio
import os

import pytest


def pytest_collection_modifyitems(items):
    """Reorder tests to run browser tests last.

    This prevents Playwright's async event loop from polluting
    other async tests that run with pytest-asyncio.
    """
    browser_tests = []
    other_tests = []

    for item in items:
        if 'browser' in item.keywords or 'e2e/browser' in str(item.fspath):
            browser_tests.append(item)
        else:
            other_tests.append(item)

    # Reorder: non-browser tests first, then browser tests
    items[:] = other_tests + browser_tests


@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop for each test function.

    This prevents event loop pollution between tests, especially when
    running browser tests (Playwright) alongside async tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


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

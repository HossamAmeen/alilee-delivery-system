"""App-level pytest config for the users app.

This file is a convenient place for user/test-specific fixtures. The project's
top-level fixtures (in `src/conftest.py`) are available here, so this file
starts small and can be expanded later.
"""

import pytest

from users.models import Driver, FirebaseDevice, Trader, UserAccount, UserRole


@pytest.fixture
def owner(db):
    """Create and return a user with OWNER role."""
    return UserAccount.objects.create_user(
        email="owner_fixture@example.com",
        password="testpass123",
        full_name="Owner Fixture",
        role=UserRole.OWNER,
    )


@pytest.fixture
def manager(db):
    """Create and return a user with MANAGER role."""
    return UserAccount.objects.create_user(
        email="manager_fixture@example.com",
        password="testpass123",
        full_name="Manager Fixture",
        role=UserRole.MANAGER,
    )


@pytest.fixture
def admin(db):
    """Create and return a user with ADMIN role."""
    return UserAccount.objects.create_user(
        email="admin_fixture@example.com",
        password="testpass123",
        full_name="Admin Fixture",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def trader(db):
    """Create and return an active trader for testing."""
    return Trader.objects.create_user(
        email="trader@example.com",
        password="testpass123",
        full_name="Test Trader",
        role=UserRole.TRADER,
        status="active",
        is_active=True,
    )


@pytest.fixture
def inactive_trader(db):
    """Create and return an inactive trader for testing."""
    return Trader.objects.create_user(
        email="inactive_trader@example.com",
        password="testpass123",
        full_name="Inactive Trader",
        role=UserRole.TRADER,
        status="inactive",
        is_active=False,
    )


@pytest.fixture
def driver(db):
    """Create and return an active driver for testing."""
    return Driver.objects.create_user(
        email="driver@example.com",
        password="testpass123",
        full_name="Test Driver",
        role=UserRole.DRIVER,
        is_active=True,
    )


@pytest.fixture
def inactive_driver(db):
    """Create and return an inactive driver for testing."""
    return Driver.objects.create_user(
        email="inactive_driver@example.com",
        password="testpass123",
        full_name="Inactive Driver",
        role=UserRole.DRIVER,
        is_active=False,
    )


@pytest.fixture
def user_client(api_client, admin):
    """Create and return an authenticated API client."""
    api_client.force_authenticate(user=admin)
    return api_client


@pytest.fixture
def firebase_device(admin):
    """Create and return a FirebaseDevice instance."""
    return FirebaseDevice.objects.create(user=admin, token="test-firebase-token-123")


@pytest.fixture
def trader_client(api_client, trader):
    """Create and return an authenticated API client for a trader."""
    api_client.force_authenticate(user=trader)
    return api_client

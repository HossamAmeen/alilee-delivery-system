"""App-level pytest config for the users app.

This file is a convenient place for user/test-specific fixtures. The project's
top-level fixtures (in `src/conftest.py`) are available here, so this file
starts small and can be expanded later.
"""

import pytest
from users.models import UserAccount, UserRole, Trader, Driver

__all__ = ["pytest"]


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
    """Create and return a Trader user."""
    return Trader.objects.create_user(
        email="trader_fixture@example.com",
        password="testpass123",
        full_name="Trader Fixture",
        role=UserRole.TRADER,
        status="active",
        is_active=True,
    )


@pytest.fixture
def driver(db):
    """Create and return a Driver user."""
    return Driver.objects.create_user(
        email="driver_fixture@example.com",
        password="testpass123",
        full_name="Driver Fixture",
        role=UserRole.DRIVER,
        is_active=True,
    )

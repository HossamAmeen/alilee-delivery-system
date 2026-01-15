import pytest
from rest_framework.test import APIClient

from geo.models import City
from users.models import Trader, UserAccount, UserRole


@pytest.fixture
def api_client():
    """Create and return an API client instance."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user for testing."""
    return UserAccount.objects.create_user(
        email="admin@example.com",
        password="testpass123",
        role=UserRole.ADMIN,
        full_name="Admin User",
        is_active=True,
        is_staff=True,
        is_superuser=True,
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
def trader_2(db):
    """Create and return an active trader for testing."""
    return Trader.objects.create_user(
        email="trader2@example.com",
        password="testpass123",
        full_name="Test Trader 2",
        role=UserRole.TRADER,
        status="active",
        is_active=True,
    )


@pytest.fixture
def driver(db):
    """Create and return an active driver for testing."""
    return UserAccount.objects.create_user(
        email="driver@example.com",
        password="testpass123",
        full_name="Test Driver",
        role=UserRole.DRIVER,
        status="active",
        is_active=True,
    )


@pytest.fixture
def admin_client(admin_user):
    """Create and return an authenticated API client with admin user."""
    api_client = APIClient()
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def driver_client(driver):
    api_client = APIClient()
    api_client.force_authenticate(user=driver)
    return api_client


@pytest.fixture
def city():
    return City.objects.create(name="Test City")

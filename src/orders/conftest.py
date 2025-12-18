from decimal import Decimal

import pytest

from geo.models import DeliveryZone
from trader_pricing.models import TraderDeliveryZone
from users.models import Driver, Trader, UserRole


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
def delivery_zone(db):
    """Create and return a delivery zone for testing."""
    return DeliveryZone.objects.create(
        name="Downtown Zone",
        cost=Decimal("15.00"),
    )


@pytest.fixture
def trader_delivery_zone(trader, delivery_zone):
    """Create and return a TraderDeliveryZone relationship."""
    return TraderDeliveryZone.objects.create(
        trader=trader,
        delivery_zone=delivery_zone,
        price=Decimal("5.00"),
    )

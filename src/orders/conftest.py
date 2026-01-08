from decimal import Decimal

import pytest

from geo.models import DeliveryZone
from orders.models import Customer, Order, OrderStatus, ProductPaymentStatus
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


@pytest.fixture
def created_order(admin_client, trader, delivery_zone, trader_delivery_zone, db):
    """Create an order via API and return the order instance."""
    # Create customer first
    customer = Customer.objects.create(
        name="John Doe",
        address="123 Main Street",
        phone="+201234567890",
        location="https://maps.google.com/?q=31.2357,30.0444",
    )

    return Order.objects.create(
        reference_code="REF12345",
        product_cost=Decimal("100.00"),
        delivery_cost=Decimal("10.00"),
        extra_delivery_cost=Decimal("5.00"),
        trader_merchant_cost=Decimal("15.00"),
        delivery_zone=delivery_zone,
        trader=trader,
        status=OrderStatus.CREATED,
        product_payment_status=ProductPaymentStatus.COD,
        note="Initial order note",
        longitude="31.235700",
        latitude="30.044400",
        customer=customer,
    )


@pytest.fixture
def assigned_order(trader, delivery_zone, driver, db):
    """Create an order via API and return the order instance."""
    # Create customer first
    customer = Customer.objects.create(
        name="John Doe", address="123 Main Street", phone="+201234567890"
    )

    return Order.objects.create(
        reference_code="REF123453",
        product_cost=Decimal("100.00"),
        delivery_cost=Decimal("10.00"),
        extra_delivery_cost=Decimal("5.00"),
        delivery_zone=delivery_zone,
        trader=trader,
        driver=driver,
        status=OrderStatus.ASSIGNED,
        product_payment_status=ProductPaymentStatus.COD,
        note="Initial order note",
        longitude="31.235700",
        latitude="30.044400",
        customer=customer,
    )


@pytest.fixture
def driver_client(api_client, driver):
    """Create and return an authenticated API client with driver user."""
    api_client.force_authenticate(user=driver)
    return api_client

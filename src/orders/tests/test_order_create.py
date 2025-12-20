"""
Unit tests for order creation endpoint using pytest.

This module tests the order creation functionality through the REST API,
ensuring proper validation, authentication, and business rules are enforced.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from geo.models import DeliveryZone
from orders.models import Order
from trader_pricing.models import TraderDeliveryZone

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def delivery_zone(db):
    """Create and return a delivery zone for testing."""
    return DeliveryZone.objects.create(
        name="Downtown Zone",
        cost=Decimal("15.00"),
    )


@pytest.fixture
def another_delivery_zone(db):
    """Create and return another delivery zone for testing."""
    return DeliveryZone.objects.create(
        name="Uptown Zone",
        cost=Decimal("20.00"),
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
def valid_order_payload(trader, delivery_zone):
    """Create and return a valid order payload for testing."""
    return {
        "reference_code": "REF12345",
        "product_cost": "100.00",
        "extra_delivery_cost": "5.00",
        "delivery_zone": delivery_zone.id,
        "trader": trader.id,
        "status": "created",
        "product_payment_status": "cod",
        "note": "Test order note",
        "longitude": "31.235700",
        "latitude": "30.044400",
        "customer": {
            "name": "John Doe",
            "address": "123 Main Street, Downtown",
            "phone": "+201234567890",
            "location": "https://maps.google.com/?q=31.2357,30.0444",
        },
    }


# ============================================================================
# TEST CASES
# ============================================================================


def test_successful_order_creation(
    admin_client, valid_order_payload, trader, delivery_zone, trader_delivery_zone
):
    """
    Test 1: Successful Order Creation

    Test that an authenticated user can successfully create an order with:
    - Valid payload
    - Valid trader and delivery zone relationship
    - Assert HTTP 201 Created
    - Assert order exists in DB
    - Assert order fields match payload
    - Assert trader is assigned correctly
    """
    url = reverse("orders-list")

    response = admin_client.post(url, data=valid_order_payload, format="json")

    # Assert HTTP 201 Created
    assert (
        response.status_code == status.HTTP_201_CREATED
    ), f"Expected 201 Created, got {response.status_code}. Response: {response.data}"

    # Assert order exists in DB
    assert Order.objects.count() == 1, "Order should be created in database"

    order = Order.objects.first()

    # Assert order fields match payload
    assert (
        order.reference_code == valid_order_payload["reference_code"]
    ), "Order reference code should match payload"
    assert (
        str(order.product_cost) == valid_order_payload["product_cost"]
    ), "Order product cost should match payload"
    assert (
        str(order.extra_delivery_cost) == valid_order_payload["extra_delivery_cost"]
    ), "Order extra delivery cost should match payload"
    assert (
        order.delivery_zone.id == valid_order_payload["delivery_zone"]
    ), "Order delivery zone should match payload"
    assert order.note == valid_order_payload["note"], "Order note should match payload"
    assert (
        str(order.longitude) == valid_order_payload["longitude"]
    ), "Order longitude should match payload"
    assert (
        str(order.latitude) == valid_order_payload["latitude"]
    ), "Order latitude should match payload"

    # Assert trader assigned correctly
    assert order.trader.id == trader.id, "Order trader should be assigned correctly"

    # Assert customer was created
    assert order.customer is not None, "Customer should be created"
    assert (
        order.customer.name == valid_order_payload["customer"]["name"]
    ), "Customer name should match payload"
    assert (
        order.customer.address == valid_order_payload["customer"]["address"]
    ), "Customer address should match payload"
    assert (
        order.customer.phone == valid_order_payload["customer"]["phone"]
    ), "Customer phone should match payload"

    # Assert delivery_cost was set from delivery_zone
    assert (
        order.delivery_cost == delivery_zone.cost
    ), "Delivery cost should be set from delivery zone"

    # Assert trader_merchant_cost was set from TraderDeliveryZone
    assert (
        order.trader_merchant_cost == trader_delivery_zone.price
    ), "Trader merchant cost should be set from TraderDeliveryZone"

    # Assert response data contains expected fields
    assert "tracking_number" in response.data, "Response should contain tracking_number"
    assert (
        response.data["tracking_number"] is not None
    ), "Tracking number should be generated"


def test_unauthorized_access(api_client, valid_order_payload):
    """
    Test 2: Unauthorized Access

    Test that unauthenticated requests are rejected:
    - No authentication token
    - Assert HTTP 401 Unauthorized or 403 Forbidden
    """
    url = reverse("orders-list")

    response = api_client.post(url, data=valid_order_payload, format="json")

    # Assert HTTP 401 or 403
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ], f"Expected 401 or 403, got {response.status_code}. Response: {response.data}"

    # Assert no order was created
    assert (
        Order.objects.count() == 0
    ), "No order should be created for unauthorized request"


def test_invalid_payload_missing_required_fields(admin_client):
    """
    Test 3: Invalid Payload - Missing Required Fields

    Test that requests with missing required fields are rejected:
    - Missing required fields (customer, delivery_zone, trader)
    - Assert HTTP 400 Bad Request
    - Assert validation error returned
    """
    url = reverse("orders-list")

    # Test missing customer
    payload_missing_customer = {
        "reference_code": "REF12345",
        "product_cost": "100.00",
        "delivery_zone": 1,
        "trader": 1,
    }

    response = admin_client.post(url, data=payload_missing_customer, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Expected 400 Bad Request for missing customer, got {response.status_code}"
    assert (
        "customer" in str(response.data).lower()
    ), "Response should indicate customer is required"

    # Test missing delivery_zone
    payload_missing_delivery_zone = {
        "reference_code": "REF12345",
        "product_cost": "100.00",
        "trader": 1,
        "customer": {
            "name": "John Doe",
            "address": "123 Main St",
            "phone": "+201234567890",
        },
    }

    response = admin_client.post(url, data=payload_missing_delivery_zone, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Expected 400 Bad Request for missing delivery_zone, got {response.status_code}"

    # Test missing trader
    payload_missing_trader = {
        "reference_code": "REF12345",
        "product_cost": "100.00",
        "delivery_zone": 1,
        "customer": {
            "name": "John Doe",
            "address": "123 Main St",
            "phone": "+201234567890",
        },
    }

    response = admin_client.post(url, data=payload_missing_trader, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Expected 400 Bad Request for missing trader, got {response.status_code}"

    # Assert no orders were created
    assert Order.objects.count() == 0, "No order should be created with invalid payload"


def test_invalid_trader_or_driver_nonexistent(
    admin_client, delivery_zone, trader_delivery_zone
):
    """
    Test 4: Invalid Trader or Driver - Non-existing IDs

    Test that requests with non-existing trader/driver IDs are rejected:
    - Non-existing trader ID
    - Non-existing driver ID
    - Assert HTTP 400 or 404
    """
    url = reverse("orders-list")

    # Test non-existing trader ID
    payload_invalid_trader = {
        "reference_code": "REF12345",
        "product_cost": "100.00",
        "delivery_zone": delivery_zone.id,
        "trader": 99999,  # Non-existing trader ID
        "customer": {
            "name": "John Doe",
            "address": "123 Main St",
            "phone": "+201234567890",
        },
    }

    response = admin_client.post(url, data=payload_invalid_trader, format="json")

    assert response.status_code in [
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_404_NOT_FOUND,
    ], f"Expected 400 or 404 for non-existing trader, got {response.status_code}"

    # Test non-existing driver ID
    valid_payload_with_invalid_driver = {
        "reference_code": "REF12345",
        "product_cost": "100.00",
        "delivery_zone": delivery_zone.id,
        "trader": trader_delivery_zone.trader.id,
        "driver": 99999,  # Non-existing driver ID
        "customer": {
            "name": "John Doe",
            "address": "123 Main St",
            "phone": "+201234567890",
        },
    }

    response = admin_client.post(
        url, data=valid_payload_with_invalid_driver, format="json"
    )

    assert response.status_code in [
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_404_NOT_FOUND,
    ], f"Expected 400 or 404 for non-existing driver, got {response.status_code}"

    # Assert no orders were created
    assert (
        Order.objects.count() == 0
    ), "No order should be created with invalid trader/driver IDs"


def test_business_rule_validation_inactive_trader(
    admin_client, inactive_trader, delivery_zone, valid_order_payload
):
    """
    Test 5: Business Rule Validation - Inactive Trader

    Test that inactive traders cannot be assigned to orders:
    - Inactive trader
    - Assert HTTP 400
    - Assert correct error message
    """
    url = reverse("orders-list")

    # Update payload to use inactive trader
    payload_with_inactive_trader = valid_order_payload.copy()
    payload_with_inactive_trader["trader"] = inactive_trader.id

    response = admin_client.post(url, data=payload_with_inactive_trader, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Expected 400 Bad Request for inactive trader, got {response.status_code}"
    assert (
        "not active" in str(response.data).lower()
        or "inactive" in str(response.data).lower()
    ), "Response should indicate trader is not active"

    # Assert no order was created
    assert Order.objects.count() == 0, "No order should be created with inactive trader"


def test_business_rule_validation_inactive_driver(
    admin_client,
    trader,
    delivery_zone,
    trader_delivery_zone,
    inactive_driver,
    valid_order_payload,
):
    """
    Test 5: Business Rule Validation - Inactive Driver

    Test that inactive drivers cannot be assigned to orders:
    - Inactive driver
    - Assert HTTP 400
    - Assert correct error message
    """
    url = reverse("orders-list")

    # Update payload to include inactive driver
    payload_with_inactive_driver = valid_order_payload.copy()
    payload_with_inactive_driver["driver"] = inactive_driver.id

    response = admin_client.post(url, data=payload_with_inactive_driver, format="json")

    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    ), f"Expected 400 Bad Request for inactive driver, got {response.status_code}"
    assert (
        "not active" in str(response.data).lower()
        or "inactive" in str(response.data).lower()
    ), "Response should indicate driver is not active"

    # Assert no order was created
    assert Order.objects.count() == 0, "No order should be created with inactive driver"


def test_business_rule_validation_trader_not_serving_delivery_zone(
    admin_client, trader, delivery_zone, another_delivery_zone, valid_order_payload
):
    """
    Test 5: Business Rule Validation - Trader Not Serving Delivery Zone

    Test that traders cannot be assigned to delivery zones they don't serve:
    - Trader not serving the delivery zone (no TraderDeliveryZone relationship)
    - Assert HTTP 400
    - Assert correct error message about trader not serving delivery zone
    """
    url = reverse("orders-list")

    # Update payload to use delivery zone that trader doesn't serve
    payload_wrong_zone = valid_order_payload.copy()
    payload_wrong_zone["delivery_zone"] = another_delivery_zone.id

    response = admin_client.post(url, data=payload_wrong_zone, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST, (
        f"Expected 400 Bad Request for trader not serving delivery zone, "
        f"got {response.status_code}. Response: {response.data}"
    )
    assert (
        "does not serve" in str(response.data).lower()
        or "delivery zone" in str(response.data).lower()
    ), (
        f"Response should indicate trader does not serve the delivery zone. "
        f"Response: {response.data}"
    )

    # Assert no order was created
    assert (
        Order.objects.count() == 0
    ), "No order should be created when trader doesn't serve the delivery zone"

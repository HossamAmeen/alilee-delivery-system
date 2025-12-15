"""
Unit tests for order update endpoint using pytest.

This module tests the order update functionality through the REST API,
ensuring proper validation, authentication, and business rules are enforced.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from geo.models import DeliveryZone
from orders.models import Order
from trader_pricing.models import TraderDeliveryZone
from users.models import Driver, Trader, UserAccount, UserRole


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def api_client():
    """Create and return an API client instance."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def user(db):
    """Create and return an authenticated user for testing."""
    return UserAccount.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        full_name="Test User",
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
def auth_client(api_client, user):
    """Create and return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def created_order(auth_client, trader, delivery_zone, trader_delivery_zone, db):
    """Create an order via API and return the order instance."""
    from orders.models import Customer
    
    # Create customer first
    customer = Customer.objects.create(
        name="John Doe",
        address="123 Main Street",
        phone="+201234567890",
        location="https://maps.google.com/?q=31.2357,30.0444",
    )
    
    order_payload = {
        "reference_code": "REF12345",
        "product_cost": "100.00",
        "extra_delivery_cost": "5.00",
        "delivery_zone": delivery_zone.id,
        "trader": trader.id,
        "status": "created",
        "payment_method": "cod",
        "product_payment_status": "cod",
        "note": "Initial order note",
        "longitude": "31.235700",
        "latitude": "30.044400",
        "customer": {
            "name": customer.name,
            "address": customer.address,
            "phone": customer.phone,
            "location": customer.location,
        },
    }
    
    url = reverse("orders-list")
    response = auth_client.post(url, data=order_payload, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    order_id = response.data["id"]
    return Order.objects.get(id=order_id)


# ============================================================================
# TEST CASES
# ============================================================================


@pytest.mark.django_db
def test_successful_order_update(auth_client, created_order, trader, delivery_zone):
    """
    Test 1: Successful Order Update
    
    Test that an authenticated user can successfully update an order:
    - Create order via API
    - Update order via API (status, note, price, etc.)
    - Assert HTTP 200
    - Assert order updated in DB
    - Assert updated fields match payload
    """
    url = reverse("orders-detail", kwargs={"pk": created_order.id})
    
    update_payload = {
        "reference_code": created_order.reference_code,
        "product_cost": "150.00",
        "extra_delivery_cost": "10.00",
        "delivery_zone": delivery_zone.id,
        "trader": trader.id,
        "status": "in_progress",
        "payment_method": "cod",
        "product_payment_status": "cod",
        "note": "Updated order note",
        "longitude": "31.240000",
        "latitude": "30.050000",
        "customer": {
            "id": created_order.customer.id,
            "name": created_order.customer.name,
            "address": "456 Updated Street",
            "phone": created_order.customer.phone,
            "location": created_order.customer.location,
        },
    }
    
    response = auth_client.put(url, data=update_payload, format="json")
    
    # Assert HTTP 200 OK
    assert response.status_code == status.HTTP_200_OK, (
        f"Expected 200 OK, got {response.status_code}. Response: {response.data}"
    )
    
    # Assert order updated in DB
    created_order.refresh_from_db()
    
    # Assert updated fields match payload
    assert str(created_order.product_cost) == update_payload["product_cost"], (
        "Product cost should be updated"
    )
    assert str(created_order.extra_delivery_cost) == update_payload["extra_delivery_cost"], (
        "Extra delivery cost should be updated"
    )
    assert created_order.status == update_payload["status"], (
        "Status should be updated"
    )
    assert created_order.note == update_payload["note"], (
        "Note should be updated"
    )
    assert str(created_order.longitude) == update_payload["longitude"], (
        "Longitude should be updated"
    )
    assert str(created_order.latitude) == update_payload["latitude"], (
        "Latitude should be updated"
    )
    assert created_order.customer.address == update_payload["customer"]["address"], (
        "Customer address should be updated"
    )


@pytest.mark.django_db
def test_unauthorized_update(api_client, created_order):
    """
    Test 2: Unauthorized Update
    
    Test that unauthenticated requests cannot update orders:
    - No authentication
    - Assert 401 / 403
    """
    url = reverse("orders-detail", kwargs={"pk": created_order.id})
    
    update_payload = {
        "reference_code": created_order.reference_code,
        "product_cost": "150.00",
        "delivery_zone": created_order.delivery_zone.id,
        "trader": created_order.trader.id,
        "customer": {
            "id": created_order.customer.id,
            "name": created_order.customer.name,
            "address": created_order.customer.address,
            "phone": created_order.customer.phone,
            "location": created_order.customer.location,
        },
    }
    
    response = api_client.put(url, data=update_payload, format="json")
    
    # Assert HTTP 401 or 403
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ], (
        f"Expected 401 or 403, got {response.status_code}. Response: {response.data}"
    )


@pytest.mark.django_db
def test_invalid_update_payload_missing_required_fields(auth_client, created_order):
    """
    Test 3: Invalid Update Payload - Missing Required Fields
    
    Test that requests with missing required fields are rejected:
    - Missing required fields (customer, delivery_zone, trader)
    - Assert HTTP 400 Bad Request
    """
    url = reverse("orders-detail", kwargs={"pk": created_order.id})
    
    # Test missing customer
    payload_missing_customer = {
        "reference_code": created_order.reference_code,
        "product_cost": "150.00",
        "delivery_zone": created_order.delivery_zone.id,
        "trader": created_order.trader.id,
    }
    
    response = auth_client.put(url, data=payload_missing_customer, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST, (
        f"Expected 400 Bad Request for missing customer, got {response.status_code}"
    )
    
    # Test missing delivery_zone
    payload_missing_delivery_zone = {
        "reference_code": created_order.reference_code,
        "product_cost": "150.00",
        "trader": created_order.trader.id,
        "customer": {
            "id": created_order.customer.id,
            "name": created_order.customer.name,
            "address": created_order.customer.address,
            "phone": created_order.customer.phone,
            "location": created_order.customer.location,
        },
    }
    
    response = auth_client.put(url, data=payload_missing_delivery_zone, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST, (
        f"Expected 400 Bad Request for missing delivery_zone, got {response.status_code}"
    )


@pytest.mark.django_db
def test_update_nonexistent_order(auth_client):
    """
    Test 4: Update Non-Existing Order
    
    Test that updating a non-existing order returns 404:
    - Non-existing order ID
    - Assert 404
    """
    url = reverse("orders-detail", kwargs={"pk": 99999})
    
    update_payload = {
        "reference_code": "REF99999",
        "product_cost": "100.00",
        "delivery_zone": 1,
        "trader": 1,
        "customer": {
            "name": "Test Customer",
            "address": "Test Address",
            "phone": "+201234567890",
        },
    }
    
    response = auth_client.put(url, data=update_payload, format="json")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND, (
        f"Expected 404 Not Found, got {response.status_code}"
    )


@pytest.mark.django_db
def test_business_rule_validation_cannot_update_delivered_order(
    auth_client, created_order, trader, delivery_zone
):
    """
    Test 5: Business Rules Validation - Cannot Update Delivered Order
    
    Test that delivered orders cannot be updated:
    - Update order status to DELIVERED via API
    - Try to update the order again
    - Assert correct error message (400 Bad Request)
    """
    # First, update order to DELIVERED
    url = reverse("orders-detail", kwargs={"pk": created_order.id})
    
    delivered_payload = {
        "reference_code": created_order.reference_code,
        "product_cost": str(created_order.product_cost),
        "extra_delivery_cost": str(created_order.extra_delivery_cost),
        "delivery_zone": delivery_zone.id,
        "trader": trader.id,
        "status": "delivered",
        "payment_method": "cod",
        "product_payment_status": "cod",
        "customer": {
            "id": created_order.customer.id,
            "name": created_order.customer.name,
            "address": created_order.customer.address,
            "phone": created_order.customer.phone,
            "location": created_order.customer.location,
        },
    }
    
    response = auth_client.put(url, data=delivered_payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    
    # Try to update the delivered order
    update_payload = {
        "reference_code": created_order.reference_code,
        "product_cost": "200.00",
        "extra_delivery_cost": str(created_order.extra_delivery_cost),
        "delivery_zone": delivery_zone.id,
        "trader": trader.id,
        "status": "delivered",
        "payment_method": "cod",
        "product_payment_status": "cod",
        "customer": {
            "id": created_order.customer.id,
            "name": created_order.customer.name,
            "address": created_order.customer.address,
            "phone": created_order.customer.phone,
            "location": created_order.customer.location,
        },
    }
    
    response = auth_client.put(url, data=update_payload, format="json")
    
    # According to the API code, it should return 400 with error message
    assert response.status_code == status.HTTP_400_BAD_REQUEST, (
        f"Expected 400 Bad Request when updating delivered order, got {response.status_code}"
    )
    assert "delivered" in str(response.data).lower() or "cannot be updated" in str(
        response.data
    ).lower(), (
        "Response should indicate delivered orders cannot be updated"
    )


@pytest.mark.django_db
def test_business_rule_validation_cannot_update_cancelled_order(
    auth_client, created_order, trader, delivery_zone
):
    """
    Test 5: Business Rules Validation - Cannot Update Cancelled Order
    
    Test that cancelled orders cannot be updated:
    - Update order status to CANCELLED via API
    - Try to update the order again
    - Assert correct error message (400 Bad Request)
    """
    # First, update order to CANCELLED
    url = reverse("orders-detail", kwargs={"pk": created_order.id})
    
    cancelled_payload = {
        "reference_code": created_order.reference_code,
        "product_cost": str(created_order.product_cost),
        "extra_delivery_cost": str(created_order.extra_delivery_cost),
        "delivery_zone": delivery_zone.id,
        "trader": trader.id,
        "status": "cancelled",
        "payment_method": "cod",
        "product_payment_status": "cod",
        "cancel_reason": "Test cancellation",
        "customer": {
            "id": created_order.customer.id,
            "name": created_order.customer.name,
            "address": created_order.customer.address,
            "phone": created_order.customer.phone,
            "location": created_order.customer.location,
        },
    }
    
    response = auth_client.put(url, data=cancelled_payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    
    # Try to update the cancelled order
    update_payload = {
        "reference_code": created_order.reference_code,
        "product_cost": "200.00",
        "extra_delivery_cost": str(created_order.extra_delivery_cost),
        "delivery_zone": delivery_zone.id,
        "trader": trader.id,
        "status": "cancelled",
        "payment_method": "cod",
        "product_payment_status": "cod",
        "customer": {
            "id": created_order.customer.id,
            "name": created_order.customer.name,
            "address": created_order.customer.address,
            "phone": created_order.customer.phone,
            "location": created_order.customer.location,
        },
    }
    
    response = auth_client.put(url, data=update_payload, format="json")
    
    # According to the API code, it should return 400 with error message
    assert response.status_code == status.HTTP_400_BAD_REQUEST, (
        f"Expected 400 Bad Request when updating cancelled order, got {response.status_code}"
    )
    assert "cancelled" in str(response.data).lower() or "cannot be updated" in str(
        response.data
    ).lower(), (
        "Response should indicate cancelled orders cannot be updated"
    )


@pytest.mark.django_db
def test_partial_update_patch(auth_client, created_order):
    """
    Test that PATCH (partial update) works correctly:
    - Update only note field
    - Assert HTTP 200
    - Assert only note is updated
    """
    url = reverse("orders-detail", kwargs={"pk": created_order.id})
    
    patch_payload = {
        "note": "Updated note via PATCH",
    }
    
    response = auth_client.patch(url, data=patch_payload, format="json")
    
    assert response.status_code == status.HTTP_200_OK, (
        f"Expected 200 OK for PATCH, got {response.status_code}"
    )
    
    created_order.refresh_from_db()
    assert created_order.note == patch_payload["note"], (
        "Note should be updated via PATCH"
    )


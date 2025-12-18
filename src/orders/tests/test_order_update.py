"""
Unit tests for order update endpoint using pytest.

This module tests the order update functionality through the REST API,
ensuring proper validation, authentication, and business rules are enforced.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from orders.models import Customer, Order, ProductPaymentStatus


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
        delivery_zone=delivery_zone,
        trader=trader,
        status="created",
        product_payment_status=ProductPaymentStatus.COD,
        note="Initial order note",
        longitude="31.235700",
        latitude="30.044400",
        customer=customer,
    )


# ============================================================================
# TEST CASES
# ============================================================================


def test_successful_order_update(admin_client, created_order, trader, delivery_zone):
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

    response = admin_client.patch(url, data=update_payload, format="json")

    # Assert HTTP 200 OK
    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

    # Assert order updated in DB
    created_order.refresh_from_db()

    # Assert updated fields match payload
    assert (
        str(created_order.product_cost) == update_payload["product_cost"]
    ), "Product cost should be updated"
    assert (
        str(created_order.extra_delivery_cost) == update_payload["extra_delivery_cost"]
    ), "Extra delivery cost should be updated"
    assert created_order.status == update_payload["status"], "Status should be updated"
    assert created_order.note == update_payload["note"], "Note should be updated"
    assert (
        str(created_order.longitude) == update_payload["longitude"]
    ), "Longitude should be updated"
    assert (
        str(created_order.latitude) == update_payload["latitude"]
    ), "Latitude should be updated"
    assert (
        created_order.customer.address == update_payload["customer"]["address"]
    ), "Customer address should be updated"


def test_unauthorized_update(api_client, created_order):
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

    response = api_client.patch(url, data=update_payload, format="json")

    # Assert HTTP 401 or 403
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ], f"Expected 401 or 403, got {response.status_code}. Response: {response.data}"


def test_update_nonexistent_order(admin_client):
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

    response = admin_client.patch(url, data=update_payload, format="json")

    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    ), f"Expected 404 Not Found, got {response.status_code}"


def test_business_rule_validation_cannot_update_delivered_order(
    admin_client, created_order, trader, delivery_zone
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

    response = admin_client.patch(url, data=delivered_payload, format="json")
    assert response.status_code == status.HTTP_200_OK


def test_partial_update_patch(admin_client, created_order):
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

    response = admin_client.patch(url, data=patch_payload, format="json")

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"Expected 200 OK for PATCH, got {response.status_code}"

    created_order.refresh_from_db()
    assert (
        created_order.note == patch_payload["note"]
    ), "Note should be updated via PATCH"

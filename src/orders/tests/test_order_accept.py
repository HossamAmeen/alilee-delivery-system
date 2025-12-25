from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from orders.models import Order, OrderStatus


@pytest.mark.django_db
class TestOrderAcceptAPIView:
    url = reverse("order-accept")

    def test_successful_order_acceptance(self, driver_client, created_order, driver):
        """Test that a driver can successfully accept an order."""

        payload = {"reference_codes": [created_order.reference_code]}

        response = driver_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["data"][0]["reference_code"] == created_order.reference_code
        )
        assert response.data["data"][0]["assigned_driver"] == driver.full_name

        # Verify DB update
        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED
        assert created_order.driver == driver

    def test_accept_multiple_orders(
        self, driver_client, created_order, trader, delivery_zone, driver
    ):
        """Test that a driver can accept multiple orders at once."""
        # Create another order
        order2 = Order.objects.create(
            reference_code="REF67890",
            product_cost=Decimal("100.00"),
            delivery_cost=Decimal("10.00"),
            extra_delivery_cost=Decimal("0.00"),
            delivery_zone=delivery_zone,
            trader=trader,
            status=OrderStatus.CREATED,
            customer=created_order.customer,
        )

        payload = {
            "reference_codes": [created_order.reference_code, order2.reference_code]
        }

        response = driver_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 2

        created_order.refresh_from_db()
        order2.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED
        assert order2.status == OrderStatus.ASSIGNED
        assert created_order.driver == driver
        assert order2.driver == driver

    def test_order_not_found(self, driver_client):
        """Test error when tracking number doesn't exist."""
        payload = {"reference_codes": ["NONEXISTENT"]}

        response = driver_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "لا توجد طلبات بهذه اكواد التعريفة" in response.data["message"]
        # When no orders are found at all, errors list is empty in the view implementation
        assert response.data["errors"] == []

    def test_invalid_order_status(self, driver_client, created_order):
        """Test error when order is not in CREATED or IN_PROGRESS status."""
        created_order.status = OrderStatus.DELIVERED
        created_order.save()

        payload = {"reference_codes": [created_order.reference_code]}

        response = driver_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "بعض الطلبات غير قابلة للقبول" in response.data["message"]
        assert any(
            created_order.reference_code in str(err) for err in response.data["errors"]
        )
        assert f"هذا الطلب {created_order.reference_code} غير قابل للقبول." in str(
            response.data["errors"]
        )

    def test_order_already_assigned(
        self, driver_client, created_order, inactive_driver
    ):
        """Test error when order already has a driver."""
        created_order.driver = inactive_driver  # Assign to another driver
        created_order.save()

        payload = {"reference_codes": [created_order.reference_code]}

        response = driver_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            f"هذا الطلب {created_order.reference_code} مخصص ل{created_order.driver.full_name}."
            in str(response.data["errors"])
        )

    def test_unauthorized_access(self, api_client, created_order):
        """Test that unauthenticated users cannot accept orders."""
        payload = {"reference_codes": [created_order.reference_code]}

        response = api_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_driver_cannot_accept(self, admin_client, created_order):
        """Test that non-driver users (e.g. admin) cannot accept orders if IsDriverPermission is enforced."""
        payload = {"reference_codes": [created_order.reference_code]}

        response = admin_client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

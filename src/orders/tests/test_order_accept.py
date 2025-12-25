from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework import status
from orders.models import Order, OrderStatus

@pytest.mark.django_db
class TestOrderAcceptAPIView:
    def test_successful_order_acceptance(self, driver_client, created_order, driver):
        """Test that a driver can successfully accept an order."""
        url = reverse("order-accept")
        payload = {
            "tracking_numbers": [created_order.tracking_number]
        }

        response = driver_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"][0]["tracking_number"] == created_order.tracking_number
        assert response.data["data"][0]["status"] == OrderStatus.ASSIGNED # The status in response is BEFORE update in the view implementation

        # Verify DB update
        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED
        assert created_order.driver == driver

    def test_accept_multiple_orders(self, driver_client, created_order, trader, delivery_zone, driver):
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
            customer=created_order.customer
        )
        
        url = reverse("order-accept")
        payload = {
            "tracking_numbers": [created_order.tracking_number, order2.tracking_number]
        }
        
        response = driver_client.post(url, data=payload, format="json")
        
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
        url = reverse("order-accept")
        payload = {
            "tracking_numbers": ["NONEXISTENT"]
        }
        
        response = driver_client.post(url, data=payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No orders available for acceptance" in response.data["message"]
        # When no orders are found at all, errors list is empty in the view implementation
        assert response.data["errors"] == []

    def test_invalid_order_status(self, driver_client, created_order):
        """Test error when order is not in CREATED or IN_PROGRESS status."""
        created_order.status = OrderStatus.DELIVERED
        created_order.save()
        
        url = reverse("order-accept")
        payload = {
            "tracking_numbers": [created_order.tracking_number]
        }
        
        response = driver_client.post(url, data=payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # The error message in api.py uses "some of orders not found." when errors list is populated
        assert "some of orders not found" in response.data["message"]
        assert any(created_order.tracking_number in str(err) for err in response.data["errors"])
        assert "cannot be accepted" in str(response.data["errors"])

    def test_order_already_assigned(self, driver_client, created_order, inactive_driver):
        """Test error when order already has a driver."""
        created_order.driver = inactive_driver # Assign to another driver
        created_order.save()
        
        url = reverse("order-accept")
        payload = {
            "tracking_numbers": [created_order.tracking_number]
        }
        
        response = driver_client.post(url, data=payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already assigned" in str(response.data["errors"])

    def test_unauthorized_access(self, api_client, created_order):
        """Test that unauthenticated users cannot accept orders."""
        url = reverse("order-accept")
        payload = {
            "tracking_numbers": [created_order.tracking_number]
        }
        
        response = api_client.post(url, data=payload, format="json")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_driver_cannot_accept(self, admin_client, created_order):
        """Test that non-driver users (e.g. admin) cannot accept orders if IsDriverPermission is enforced."""
        url = reverse("order-accept")
        payload = {
            "tracking_numbers": [created_order.tracking_number]
        }
        
        response = admin_client.post(url, data=payload, format="json")
        
        # Depending on how IsDriverPermission is implemented, this might be 403
        assert response.status_code == status.HTTP_403_FORBIDDEN

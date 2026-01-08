from notifications.models import Notification
import pytest
from django.urls import reverse
from rest_framework import status
from orders.models import Order, OrderStatus
from users.models import Driver
from decimal import Decimal

@pytest.mark.django_db
class TestOrderDriverAssignAPIView:
    def test_assign_orders_success(self, admin_client, driver, created_order):
        """Test that an admin can assign multiple unassigned orders to a driver."""
        # Create another unassigned order
        order2 = Order.objects.create(
            reference_code="REF99999",
            product_cost=Decimal("50.00"),
            trader=created_order.trader,
            delivery_zone=created_order.delivery_zone,
            customer=created_order.customer,
            status=OrderStatus.CREATED
        )
        
        url = reverse("order-bulk-assign-driver")
        data = {
            "driver": driver.id,
            "tracking_numbers": [created_order.tracking_number, order2.tracking_number]
        }
        
        response = admin_client.patch(url, data, format="json")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        
        created_order.refresh_from_db()
        order2.refresh_from_db()
        
        assert created_order.driver == driver
        assert created_order.status == OrderStatus.ASSIGNED
        assert order2.driver == driver
        assert order2.status == OrderStatus.ASSIGNED

        assert Notification.objects.filter(user_account=driver).count() == 2

    def test_assign_orders_already_assigned(self, admin_client, driver, assigned_order):
        """Test that assigning an order that already has a driver fails."""
        url = reverse("order-bulk-assign-driver")
        data = {
            "driver": driver.id,
            "tracking_numbers": [assigned_order.tracking_number]
        }
        
        response = admin_client.patch(url, data, format="json")
        
        # The view raises CustomValidationError if no orders are available for assignment
        # because the filter excludes orders with driver__isnull=False
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No orders available for assignment" in response.data["message"]

    def test_assign_orders_partial_success_fails(self, admin_client, driver, created_order, assigned_order):
        """Test that if some orders are already assigned, the entire request fails."""
        url = reverse("order-bulk-assign-driver")
        data = {
            "driver": driver.id,
            "tracking_numbers": [created_order.tracking_number, assigned_order.tracking_number]
        }
        
        response = admin_client.patch(url, data, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "One or more orders cannot be assigned" in response.data["message"]
        
        # Verify created_order was NOT assigned (transactional integrity check)
        created_order.refresh_from_db()
        assert created_order.driver is None
        assert created_order.status == OrderStatus.CREATED

    def test_assign_orders_non_existent(self, admin_client, driver):
        """Test that assigning non-existent tracking numbers fails."""
        url = reverse("order-bulk-assign-driver")
        data = {
            "driver": driver.id,
            "tracking_numbers": ["NONEXISTENT"]
        }
        
        response = admin_client.patch(url, data, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No orders available for assignment" in response.data["message"]

    def test_unauthenticated_access(self, api_client, driver, created_order):
        """Test that unauthenticated users cannot access the endpoint."""
        url = reverse("order-bulk-assign-driver")
        data = {
            "driver": driver.id,
            "tracking_numbers": [created_order.tracking_number]
        }
        
        response = api_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

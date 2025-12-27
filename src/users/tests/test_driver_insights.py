from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from geo.models import DeliveryZone
from orders.models import Customer, Order, OrderStatus, ProductPaymentStatus
from users.models import Trader, UserRole


@pytest.mark.django_db
class TestDriverInsightsAPIView:
    url = reverse("driver-insights")

    def test_driver_insights_success(self, driver_client, driver):
        """Test retrieving driver insights successfully."""
        delivery_zone = DeliveryZone.objects.create(
            name="Downtown Zone",
            cost=Decimal("15.00"),
        )
        # Create some orders for the driver
        customer = Customer.objects.create(
            name="Test Customer",
            address="Test Address",
            phone="+201234567890",
        )
        trader = Trader.objects.create_user(
            email="trader23@example.com",
            password="testpass123",
            full_name="Test Trader",
            role=UserRole.TRADER,
            status="active",
            is_active=True,
        )

        # Delivered order
        order = Order.objects.create(
            driver=driver,
            trader=trader,
            status=OrderStatus.DELIVERED,
            delivery_cost=Decimal("20.00"),
            reference_code="TEST-888",
            extra_delivery_cost=Decimal("5.00"),
            customer=customer,
            delivery_zone=delivery_zone,
            product_payment_status=ProductPaymentStatus.COD,
            product_cost=Decimal("100.00"),
        )
        order.status = OrderStatus.DELIVERED
        order.save()

        # Assigned order
        Order.objects.create(
            driver=driver,
            trader=trader,
            status=OrderStatus.ASSIGNED,
            delivery_cost=Decimal("20.00"),
            reference_code="TEST-999",
            customer=customer,
            delivery_zone=delivery_zone,
            product_payment_status=ProductPaymentStatus.COD,
            product_cost=Decimal("100.00"),
        )

        response = driver_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["delivered"] == 1
        assert response.data["assigned_order_count"] == 1
        assert Decimal(str(response.data["total_earnings"])) == Decimal("25.00")
        driver.refresh_from_db()
        assert Decimal(str(response.data["balance"])) == driver.balance

    def test_driver_insights_date_filtering(self, driver_client, driver):
        """Test driver insights with date filtering."""
        delivery_zone = DeliveryZone.objects.create(
            name="Downtown Zone",
            cost=Decimal("15.00"),
        )
        customer = Customer.objects.create(
            name="Test Customer",
            address="Test Address",
            phone="+201234567890",
        )
        trader = Trader.objects.create_user(
            email="trader23@example.com",
            password="testpass123",
            full_name="Test Trader",
            role=UserRole.TRADER,
            status="active",
            is_active=True,
        )

        # Order from today
        Order.objects.create(
            driver=driver,
            trader=trader,
            status=OrderStatus.DELIVERED,
            delivery_cost=Decimal("30.00"),
            reference_code="TEST-123",
            customer=customer,
            delivery_zone=delivery_zone,
            product_payment_status=ProductPaymentStatus.COD,
            product_cost=Decimal("100.00"),
            created=date.today(),
        )

        # Filter for today only
        response = driver_client.get(self.url, {"start_date": date.today().isoformat()})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["delivered"] == 0
        assert Decimal(str(response.data["total_earnings"])) == Decimal("0.00")

        # Filter for yesterday only
        response = driver_client.get(
            self.url,
            {
                "start_date": date.today().isoformat(),
                "end_date": date.today().isoformat(),
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["delivered"] == 0
        assert Decimal(str(response.data["total_earnings"])) == Decimal("0.00")

    def test_driver_insights_unauthorized_non_driver(self, user_client, db):
        """Test that a non-driver user cannot access driver insights."""
        response = user_client.get(self.url)
        # Should be 403 because user_client is authenticated as admin, but not a driver
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_driver_insights_unauthenticated(self, api_client, db):
        """Test that unauthenticated users cannot access driver insights."""
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

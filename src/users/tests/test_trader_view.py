import pytest
from django.urls import reverse
from rest_framework import status
from users.models import Trader, TraderStatus, UserRole
from transactions.models import UserAccountTransaction, TransactionType
from orders.models import Order, OrderStatus
from decimal import Decimal

@pytest.mark.django_db
class TestTraderViewSet:
    def test_list_traders(self, admin_client, trader):
        """Test that an admin can list traders."""
        url = reverse("traders-list")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1
        # Check if the trader we created is in the list
        emails = [t["email"] for t in response.data["results"]]
        assert trader.email in emails
        assert "total_sales" in response.data["results"][0]
        assert "orders_count" in response.data["results"][0]

    def test_retrieve_trader(self, admin_client, trader):
        """Test that an admin can retrieve a specific trader."""
        url = reverse("traders-detail", kwargs={"pk": trader.pk})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == trader.email
        assert "total_sales" in response.data
        assert "orders_count" in response.data

    def test_create_trader(self, admin_client):
        """Test that an admin can create a new trader."""
        url = reverse("traders-list")
        data = {
            "email": "new_trader@example.com",
            "full_name": "New Trader",
            "phone_number": "01234567890",
            "password": "newpassword123",
        }
        response = admin_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Trader.objects.filter(email=data["email"]).exists()
        trader = Trader.objects.get(email=data["email"])
        assert trader.role == UserRole.TRADER

    def test_update_trader(self, user_client, trader):
        """Test that an admin can update a trader."""
        url = reverse("traders-detail", kwargs={"pk": trader.pk})
        data = {"full_name": "Updated Trader Name"}
        response = user_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        trader.refresh_from_db()
        assert trader.full_name == "Updated Trader Name"

    def test_delete_trader(self, user_client, trader):
        """Test that an admin can delete a trader."""
        url = reverse("traders-detail", kwargs={"pk": trader.pk})
        response = user_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Trader.objects.filter(pk=trader.pk).exists()

    def test_trader_annotations(self, user_client, trader, db):
        """Test that total_sales and orders_count are correctly annotated."""
        # Create an order for the trader
        order = Order.objects.create(trader=trader, product_cost=Decimal("100.00"))
        
        # Create a transaction for the trader linked to the order
        UserAccountTransaction.objects.create(
            user_account=trader,
            amount=Decimal("50.00"),
            transaction_type=TransactionType.WITHDRAW,
            order=order,
            is_rolled_back=False
        )
        
        url = reverse("traders-detail", kwargs={"pk": trader.pk})
        response = user_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["orders_count"] == 1
        assert Decimal(response.data["total_sales"]) == Decimal("50.00")

    def test_trader_retrieve_date_filter(self, user_client, trader):
        """Test the retrieve action with date filter (smoke test)."""
        url = reverse("traders-detail", kwargs={"pk": trader.pk})
        response = user_client.get(url, {"date": "2023-01-01"})
        assert response.status_code == status.HTTP_200_OK
        # The logic for filtering prices by date is in the serializer method field
        # and depends on trader_delivery_zones_trader which we haven't mocked here,
        # but we verify the endpoint handles the parameter.

    def test_unauthenticated_access(self, api_client, trader):
        """Test that unauthenticated users cannot access traders."""
        url = reverse("traders-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

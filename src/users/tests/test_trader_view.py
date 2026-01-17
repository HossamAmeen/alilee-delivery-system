from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from orders.models import Order
from transactions.models import TransactionType, UserAccountTransaction
from users.models import Trader, UserRole


@pytest.mark.django_db
class TestTraderViewSet:
    def setup_method(self):
        """Setup method to run before each test."""
        self.list_url = reverse("traders-list")
        self.detail_url = lambda id: reverse("traders-detail", args=[id])

        pass

    def test_list_traders(self, admin_client, trader):
        """Test that an admin can list traders."""
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["email"] == trader.email
        assert response.data["results"][0]["full_name"] == trader.full_name
        assert response.data["results"][0]["phone_number"] == trader.phone_number
        assert Decimal(response.data["results"][0]["total_sales"]) == 0
        assert response.data["results"][0]["orders_count"] == 0

    def test_retrieve_trader(self, admin_client, trader):
        """Test that an admin can retrieve a specific trader."""
        url = reverse("traders-detail", kwargs={"pk": trader.pk})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == trader.email
        assert Decimal(response.data["total_sales"]) == 0
        assert response.data["orders_count"] == 0

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
            is_rolled_back=False,
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
        
    def test_delete_trader_with_zero_balance(self, user_client, trader):
        """Test deleting a trader with zero balance."""
        trader.balance = Decimal('0.00')
        trader.save()
        
        url = reverse("traders-detail", kwargs={"pk": trader.pk})
        response = user_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Trader.objects.filter(pk=trader.pk).exists()

    @pytest.mark.django_db(transaction=True)
    def test_delete_trader_with_positive_balance(self, user_client, trader):
        """Test cannot delete trader with positive balance."""
        trader.balance = Decimal('200.00')
        trader.save()
        
        url = reverse("traders-detail", kwargs={"pk": trader.pk})
        response = user_client.delete(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Trader.objects.filter(pk=trader.pk).exists()
        assert 'لا يمكن حذف التاجر' in str(response.data)
        assert '200.00' in str(response.data)

    @pytest.mark.django_db(transaction=True)
    def test_delete_trader_with_negative_balance(self, user_client, trader):
        """Test cannot delete trader with negative balance."""
        trader.balance = Decimal('-75.50')
        trader.save()
        
        url = reverse("traders-detail", kwargs={"pk": trader.pk})
        response = user_client.delete(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Trader.objects.filter(pk=trader.pk).exists()
        assert 'لا يمكن حذف التاجر' in str(response.data)
        assert '-75.50' in str(response.data)

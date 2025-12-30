import pytest
from django.urls import reverse
from rest_framework import status
from transactions.models import UserAccountTransaction, TransactionType

@pytest.mark.django_db
class TestUserAccountTransactionViewSet:
    def test_list_transactions(self, admin_client, transaction):
        url = reverse("user-transactions-list")
        response = admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # The response is paginated, so we check 'results'
        assert len(response.data["results"]) >= 1
        assert response.data["results"][0]["id"] == transaction.id

    def test_create_transaction(self, admin_client, admin_user):
        url = reverse("user-transactions-list")
        data = {
            "user_account": admin_user.id,
            "amount": "50.00",
            "transaction_type": TransactionType.WITHDRAW,
            "notes": "New withdrawal"
        }
        response = admin_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert UserAccountTransaction.objects.filter(amount=50.00).exists()

        data = {
            "user_account": admin_user.id,
            "amount": "100.00",
            "transaction_type": TransactionType.DEPOSIT,
            "notes": "New deposit"
        }
        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert UserAccountTransaction.objects.filter(amount=100.00).exists()

        data = {
            "user_account": admin_user.id,
            "amount": "130.00",
            "transaction_type": TransactionType.EXPENSE,
            "notes": "New expense"
        }
        response = admin_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert UserAccountTransaction.objects.filter(amount=130.00).exists()

    def test_filter_transactions_by_user(self, admin_client, transaction, admin_user):
        url = reverse("user-transactions-list")
        response = admin_client.get(url, {"user_account": admin_user.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert all(item["user_account"]["id"] == admin_user.id for item in response.data["results"])

    def test_filter_transactions_by_type(self, admin_client, transaction):
        url = reverse("user-transactions-list")
        # Filter for DEPOSIT
        response = admin_client.get(url, {"transaction_type": TransactionType.DEPOSIT})
        assert response.status_code == status.HTTP_200_OK
        assert any(item["transaction_type"] == TransactionType.DEPOSIT for item in response.data["results"])
        
        # Filter for WITHDRAW (should be empty if only the fixture exists)
        response = admin_client.get(url, {"transaction_type": TransactionType.WITHDRAW})
        assert response.status_code == status.HTTP_200_OK
        assert all(item["transaction_type"] != TransactionType.DEPOSIT for item in response.data["results"])

    def test_unauthenticated_access(self, api_client):
        url = reverse("user-transactions-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from transactions.models import Expense, TransactionType, UserAccountTransaction


@pytest.mark.django_db
class TestExpenseFunctionality:
    def test_create_expense_transaction_creates_expense_object(self, driver):
        # Initial balance should be 0
        assert driver.balance == Decimal("0.00")

        # Create an EXPENSE transaction
        transaction = UserAccountTransaction.objects.create(
            user_account_id=driver.id,
            amount=Decimal("150.00"),
            transaction_type=TransactionType.EXPENSE,
            notes="Office supplies",
        )

        # Verify Expense object was created via signal
        expense = Expense.objects.filter(transaction=transaction).first()
        assert expense is not None
        assert expense.cost == Decimal("150.00")
        assert expense.description == f"{transaction.notes} (محصلة من عمليه مالية)"

        # Verify balance was updated (decreased)
        driver.refresh_from_db()
        assert driver.balance == Decimal("-150.00")

    def test_delete_expense_triggers_rollback(self, driver):
        # Create an EXPENSE transaction
        transaction = UserAccountTransaction.objects.create(
            user_account_id=driver.id,
            amount=Decimal("200.00"),
            transaction_type=TransactionType.EXPENSE,
            notes="Travel expense",
        )

        expense = Expense.objects.get(transaction=transaction)

        # Verify initial state
        driver.refresh_from_db()
        assert driver.balance == Decimal("-200.00")

        # Delete the expense
        expense.delete()

        # Verify original transaction is marked as rolled back
        transaction.refresh_from_db()
        assert transaction.is_rolled_back is True
        assert "(استرجاع)" in transaction.notes

        # Verify a new WITHDRAW transaction was created to reverse the expense
        # Note: The signal uses WITHDRAW to ADD back the balance because update_balance(amount) adds the amount.
        # In UserAccountTransaction signal: WITHDRAW -> update_balance(amount)
        rollback_transaction = UserAccountTransaction.objects.filter(
            user_account=driver,
            transaction_type=TransactionType.WITHDRAW,
            notes="مبلغ مسترجع الخاص المصارف",
        ).first()
        assert rollback_transaction is not None
        assert rollback_transaction.amount == Decimal("200.00")

        # Verify balance was updated (increased back to 0)
        driver.refresh_from_db()
        assert driver.balance == Decimal("0.00")
        # Both the original transaction and the new rollback transaction are marked as is_rolled_back
        assert UserAccountTransaction.objects.filter(is_rolled_back=True).count() == 2


@pytest.mark.django_db
class TestExpenseAPI:
    def setup_method(self):
        self.url = reverse("expenses-list")

    def test_create_expense(self, admin_client):
        data = {
            "description": "New Office Chair",
            "cost": "120.50",
            "date": "2026-01-17",
        }
        response = admin_client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["description"] == "New Office Chair"
        assert response.data["cost"] == "120.50"
        assert Expense.objects.filter(description="New Office Chair").exists()

    def test_retrieve_expense(self, admin_client):
        expense = Expense.objects.create(
            description="Coffee", cost=Decimal("5.00"), date="2026-01-17"
        )
        url = reverse("expenses-detail", kwargs={"pk": expense.id})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == "Coffee"

    def test_update_expense(self, admin_client):
        expense = Expense.objects.create(
            description="Old Desk", cost=Decimal("50.00"), date="2026-01-17"
        )
        url = reverse("expenses-detail", kwargs={"pk": expense.id})
        data = {"description": "New Desk", "cost": "75.00"}
        response = admin_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == "New Desk"
        assert response.data["cost"] == "75.00"

        expense.refresh_from_db()
        assert expense.description == "New Desk"
        assert expense.cost == Decimal("75.00")

    def test_list_expenses_with_filters(self, admin_client, driver):
        
        Expense.objects.create(description="Jan Expense", cost=10, date="2025-01-01")
        Expense.objects.create(description="Feb Expense", cost=20, date="2025-02-01")
        transaction = UserAccountTransaction.objects.create(
            user_account_id=driver.id,
            amount=Decimal("200.00"),
            transaction_type=TransactionType.EXPENSE,
            notes="Travel expense",
        ) # this create expense with transaction

        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        
        expenses = response.data["results"]["expenses"]
        assert expenses[0]["description"] == f"{transaction.notes} (محصلة من عمليه مالية)"
        assert expenses[1]["description"] == "Feb Expense"
        assert expenses[2]["description"] == "Jan Expense"
        assert expenses[0]["cost"] == "200.00"
        assert expenses[1]["cost"] == "20.00"
        assert expenses[2]["cost"] == "10.00"
        assert expenses[0]["date"] == transaction.created.strftime("%Y-%m-%d")
        assert expenses[1]["date"] == "2025-02-01"
        assert expenses[2]["date"] == "2025-01-01"
        assert expenses[0]["transaction"]["id"] == transaction.id
        assert expenses[0]["transaction"]["notes"] == transaction.notes
        assert expenses[0]["transaction"]["user_account"]["id"] == driver.id
        assert expenses[0]["transaction"]["user_account"]["role"] == driver.role
        assert expenses[1]["transaction"] == None
        assert expenses[2]["transaction"] == None

        # Filter for January
        response = admin_client.get(
            self.url, {"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )
        assert response.status_code == status.HTTP_200_OK
        # Results are in results['expenses'] because of custom list implementation
        expenses = response.data["results"]["expenses"]
        assert len(expenses) == 1
        assert expenses[0]["description"] == "Jan Expense"

        # Filter for February
        response = admin_client.get(self.url, {"start_date": "2025-02-01"})
        expenses = response.data["results"]["expenses"]
        assert len(expenses) == 2
        assert expenses[0]["description"] == f"{transaction.notes} (محصلة من عمليه مالية)"
        assert expenses[1]["description"] == "Feb Expense"

    def test_delete_expense_standalone(self, admin_client):
        expense = Expense.objects.create(
            description="To be deleted", cost=10, date="2025-01-17"
        )
        url = reverse("expenses-detail", kwargs={"pk": expense.id})
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Expense.objects.filter(id=expense.id).exists()

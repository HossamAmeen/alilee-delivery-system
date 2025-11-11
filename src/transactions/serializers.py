from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from rest_framework.serializers import ModelSerializer

from transactions.models import Expense, TransactionType, UserAccountTransaction
from users.models import Trader
from utilities.exceptions import CustomValidationError


class UserAccountTransactionSerializer(ModelSerializer):
    class Meta:
        model = UserAccountTransaction
        fields = [
            "id",
            "user_account",
            "amount",
            "transaction_type",
            "file",
            "notes",
            "created",
            "modified",
        ]
        read_only_fields = ("id", "created", "modified")

    @atomic
    def create(self, validated_data):
        trader = get_object_or_404(Trader, pk=validated_data["user_account"])
        if (
            validated_data["transaction_type"] == TransactionType.WITHDRAW
            and validated_data["amount"] > trader.balance
        ):
            raise CustomValidationError("Trader's balance is not enough.")

        trader_transaction = super().create(validated_data)
        if validated_data["transaction_type"] == TransactionType.WITHDRAW:
            trader.balance -= validated_data["amount"]
        elif validated_data["transaction_type"] == TransactionType.DEPOSIT:
            trader.balance += validated_data["amount"]

        trader.save()
        return trader_transaction


class ExpenseSerializer(ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            "id",
            "date",
            "cost",
            "description",
            "created",
            "modified",
        ]
        read_only_fields = ("id", "created", "modified")

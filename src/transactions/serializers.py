from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from rest_framework import serializers
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


class FinancialInsightsSerializer(serializers.Serializer):
    start_date = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    end_date = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    total_revenue = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_expenses = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    net_profit = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    shipments_completed = serializers.IntegerField(read_only=True)
    pending_receivables = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    pending_payables = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    def validate(self, data):
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError("start_date cannot be after end_date.")
        return data

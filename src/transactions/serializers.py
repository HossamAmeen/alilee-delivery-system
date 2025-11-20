from django.db.transaction import atomic
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from transactions.models import (
    Expense, TransactionType, UserAccountTransaction
)
from orders.models import Order
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

    def to_representation(self, instance):
        start_date = instance['start_date']
        end_date = instance['end_date']
        total_revenue = UserAccountTransaction.objects.filter(
            created__range=(start_date, end_date),
            transaction_type=TransactionType.DEPOSIT
        ).aggregate(total=Sum('amount'))['total'] or 0
        total_expenses = UserAccountTransaction.objects.filter(
            created__range=(start_date, end_date),
            transaction_type=TransactionType.WITHDRAW
        ).aggregate(total=Sum('amount'))['total'] or 0

        net_profit = total_revenue - total_expenses
        order_completed = Order.objects.filter(
            created__range=(start_date, end_date)
        ).count()

        pending_receivables = 0  # will take real value later
        pending_payables = 0     # will take real value later
        balance = total_revenue - total_expenses

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "shipments_completed": order_completed,
            "pending_receivables": pending_receivables,
            "pending_payables": pending_payables,
            "balance": balance,
        }
from datetime import date

from django.db.models import F, Sum
from django.db.models.functions import TruncMonth
from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from orders.models import Order
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
    start_date = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )
    end_date = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )
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
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    monthlyExpensesData = serializers.DictField(read_only=True)

    def validate(self, data):
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and start > end:
            raise CustomValidationError("start_date cannot be after end_date.")
        return data

    def to_representation(self, instance):
        today = date.today()

        start_date = instance.get("start_date") or today.replace(day=1)
        end_date = instance.get("end_date") or today

        monthly_revenue = (
            Order.objects.filter(created__range=(start_date, end_date))
            .annotate(month=TruncMonth("created"))
            .values("month")
            .annotate(
                total_income=Sum("trader_merchant_cost"),
                total_delivery_expense=Sum(
                    F("delivery_cost") + F("extra_delivery_cost"),
                ),
            )
            .order_by("month")
        )
        total_income, total_delivery_expense = 0, 0
        converted_monthly = {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec",
        }
        monthlyExpensesData = []
        for item in monthly_revenue:
            total_income += item["total_income"] or 0
            total_delivery_expense += item["total_delivery_expense"] or 0
            monthlyExpensesData.append(
                {
                    "name": converted_monthly[item["month"].month],
                    "total_income": float(item["total_income"] or 0),
                    "total_delivery_expense": float(
                        item["total_delivery_expense"] or 0
                    ),
                    "net_profit": float(
                        (item["total_income"] or 0)
                        - (item["total_delivery_expense"] or 0)
                    ),
                }
            )

        operational_expenses = (
            Expense.objects.filter(date__range=(start_date, end_date)).aggregate(
                total=Sum("cost")
            )["total"]
            or 0
        )
        order_completed = Order.objects.filter(
            created__range=(start_date, end_date)
        ).count()

        pending_receivables = 0
        pending_payables = 0

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": total_income,
            "total_expenses": (total_delivery_expense + operational_expenses),
            "net_profit": total_income
            - (total_delivery_expense + operational_expenses),
            "shipments_completed": order_completed,
            "pending_receivables": pending_receivables,
            "pending_payables": pending_payables,
            "monthlyExpensesData": monthlyExpensesData,
        }

from datetime import date

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncMonth
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from orders.models import Order, OrderStatus
from transactions.models import Expense, UserAccountTransaction
from users.serializers.user_account_serializers import SingleUserAccountSerializer
from utilities.exceptions import CustomValidationError


class UserAccountTransactionSerializer(ModelSerializer):
    class Meta:
        model = UserAccountTransaction
        fields = [
            "id",
            "user_account",
            "amount",
            "transaction_type",
            "is_rolled_back",
            "order",
            "file",
            "notes",
            "created",
            "modified",
        ]
        read_only_fields = ("id", "created", "modified")


class ListUserAccountTransactionSerializer(ModelSerializer):
    user_account = SingleUserAccountSerializer()

    class Meta:
        model = UserAccountTransaction
        fields = [
            "id",
            "user_account",
            "amount",
            "transaction_type",
            "is_rolled_back",
            "order",
            "file",
            "notes",
            "created",
            "modified",
        ]


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

        start_date = instance.get("start_date", today.replace(day=1))
        end_date = instance.get("end_date", today)

        monthly_revenue = (
            Order.objects.filter(
                created__range=(start_date, end_date), status=OrderStatus.DELIVERED
            )
            .annotate(month=TruncMonth("created"))
            .values("month")
            .annotate(
                total_income=Sum("trader_merchant_cost"),
                total_delivery_expense=Sum(
                    F("delivery_cost") + F("extra_delivery_cost"),
                ),
                IDs_count=Count("id"),
            )
            .order_by("month")
        )

        total_income = total_delivery_expense = total_commissions = 0
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
        shipments_per_month = []
        month_statistices = {}

        for item in monthly_revenue:
            month_statistices["month"] = converted_monthly[item["month"].month]
            month_statistices["shipment_count"] = item["IDs_count"]
            shipments_per_month.append(month_statistices)
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

        orders_statistics_qs = Order.objects.values("status").annotate(count=Count("id"))
        orders_statistics = {
            "delivered_order_count": 0,
            "cancelled_order_count": 0,
            "created__order_count": 0,
            "assigned_to_driver": 0,
            "in_progress_order_count": 0,
            "postponed_order_count": 0,
        }

        status_map = {
            OrderStatus.DELIVERED: "delivered_order_count",
            OrderStatus.CANCELLED: "cancelled_order_count",
            OrderStatus.CREATED: "created__order_count",
            OrderStatus.ASSIGNED: "assigned_to_driver",
            OrderStatus.IN_PROGRESS: "in_progress_order_count",
            OrderStatus.POSTPONED: "postponed_order_count",
        }

        total_count = 0
        for item in orders_statistics_qs:
            status = item["status"]
            count = item["count"]
            total_count += count
            if status in status_map:
                orders_statistics[status_map[status]] = count
        orders_statistics["total_count"] = total_count
        operational_expenses = (
            Expense.objects.filter(date__range=(start_date, end_date)).aggregate(
                total=Sum("cost")
            )["total"]
            or 0
        )
        shipments_per_month = [
            {"month": "يناير", "shipment_count": 27446.0},
            {"month": "فبراير", "shipment_count": 25524.0},
            {"month": "مارس", "shipment_count": 26487.0},
            {"month": "ابريل", "shipment_count": 24981.0},
            {"month": "مايو", "shipment_count": 29135.0},
            {"month": "يونيو", "shipment_count": 21013.0},
            {"month": "يوليو", "shipment_count": 25751.0},
            {"month": "اغسطس", "shipment_count": 21456.0},
            {"month": "سبتمبر", "shipment_count": 15715.0},
            {"month": "اكتوبر", "shipment_count": 21957.0},
            {"month": "نوفمبر", "shipment_count": 10458.0},
        ]
        monthly_expenses_data = [
            {
                "name": "Jan",
                "total_income": 950.0,
                "total_delivery_expense": 820.0,
                "net_profit": 130.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Feb",
                "total_income": 1100.0,
                "total_delivery_expense": 980.0,
                "net_profit": 120.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Mar",
                "total_income": 3200.0,
                "total_delivery_expense": 1500.0,
                "net_profit": 1700.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Apr",
                "total_income": 450.0,
                "total_delivery_expense": 520.0,
                "net_profit": -70.0,
                "total_commissions": 100.0,
            },
            {
                "name": "May",
                "total_income": 300.0,
                "total_delivery_expense": 310.0,
                "net_profit": -10.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Jun",
                "total_income": 780.0,
                "total_delivery_expense": 720.0,
                "net_profit": 60.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Jul",
                "total_income": 610.0,
                "total_delivery_expense": 590.0,
                "net_profit": 20.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Aug",
                "total_income": 1200.0,
                "total_delivery_expense": 1000.0,
                "net_profit": 200.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Sep",
                "total_income": 1600.0,
                "total_delivery_expense": 1400.0,
                "net_profit": 200.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Oct",
                "total_income": 2000.0,
                "total_delivery_expense": 1500.0,
                "net_profit": 500.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Nov",
                "total_income": 900.0,
                "total_delivery_expense": 950.0,
                "net_profit": -50.0,
                "total_commissions": 100.0,
            },
            {
                "name": "Dec",
                "total_income": 127.0,
                "total_delivery_expense": 1317.0,
                "net_profit": -1190.0,
                "total_commissions": 100.0,
            },
        ]

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": total_income,
            "total_commissions": total_commissions,
            "total_expenses": (total_delivery_expense + operational_expenses),
            "net_profit": (
                total_income - (total_delivery_expense + operational_expenses) - total_commissions
            ),
            "shipments_completed": monthly_revenue.count(),
            "shipments_per_month": shipments_per_month,
            "monthly_expenses_data": monthly_expenses_data,
            "orders": orders_statistics,
            "pending_earnings": 0,
            "unpaid_obligations": 0,
            "unpaid_obligations_drivers": 0,
            "unpaid_obligations_traders": 0,
        }

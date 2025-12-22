from datetime import date

from django.db.models import Case, Count, DecimalField, F, Sum, Value, When
from django.db.models.functions import TruncMonth
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from orders.models import Order, OrderStatus
from transactions.models import Expense, UserAccountTransaction
from users.serializers.user_account_serializers import SingleUserAccountSerializer
from utilities.exceptions import CustomValidationError

DEFAULT_START_DATE = "1024-12-01"

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
    # Represent 'summary_start_date'
    start_date = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )
    # Represent 'summary_end_date'
    end_date = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )
    monthly_start_date = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )
    monthly_end_date = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )
    shipment_start_date = serializers.DateField(
        format="%Y-%m-%d", input_formats=["%Y-%m-%d"], required=False
    )
    shipment_end_date = serializers.DateField(
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
    monthly_expenses_data = serializers.DictField(read_only=True)

    def validate(self, data):
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and start > end:
            raise CustomValidationError("start_date cannot be after end_date.")
        return data

    def to_representation(self, instance):
        today = date.today()

        summary_start_date = instance.get("summary_start_date", today.replace(day=1))
        summary_end_date = instance.get("summary_end_date", today)

        monthly_start_date = instance.get("monthly_start_date",DEFAULT_START_DATE)
        monthly_end_date = instance.get("monthly_end_date", today)

        shipment_start_date = instance.get("shipment_start_date", DEFAULT_START_DATE)
        shipment_end_date = instance.get("shipment_end_date", today)


        accepted_statuses = [OrderStatus.DELIVERED, OrderStatus.CANCELLED]

        summary_revenue = Order.objects.filter(
            created__range=(summary_start_date, summary_end_date),
            status__in=accepted_statuses).aggregate(
                total_revenue=Sum("trader_merchant_cost"),

                total_commissions=Sum(
                    Case(
                        When(
                            status=OrderStatus.DELIVERED,
                            then=F("delivery_cost") + F("extra_delivery_cost"),
                        ),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
            )

        summary_expense = (
            Expense.objects.filter(
                date__range=(summary_start_date, summary_end_date)
            )
            .aggregate(total_expense=Sum("cost"))
        )["total_expense"] or 0

        monthly_revenue = (
            Order.objects.filter(
                created__range=(monthly_start_date, monthly_end_date),
                status__in=accepted_statuses,
            )
            .annotate(month=TruncMonth("created"))
            .values("month")
            .annotate(
                total_income=Sum("trader_merchant_cost"),

                total_commissions=Sum(
                    Case(
                        When(
                            status=OrderStatus.DELIVERED,
                            then=F("delivery_cost") + F("extra_delivery_cost"),
                        ),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
            )
            .order_by("month")
        )

        monthly_expenses = (
            Expense.objects.filter(
                date__range=(monthly_start_date, monthly_end_date)
            )
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(monthly_expense=Sum("cost"))
        )

        expenses_by_month = {
            item["month"].month: item["monthly_expense"] or 0
            for item in monthly_expenses
        }

        total_income = total_commissions = 0
        converted_monthly = {
            1: "يناير",
            2: "فبراير",
            3: "مارس",
            4: "أبريل",
            5: "مايو",
            6: "يونيو",
            7: "يوليو",
            9: "سبتمبر",
            10: "أكتوبر",
            11: "نوفمبر",
            12: "ديسمبر",
        }

        monthly_expenses_data = []
        shipments_per_month = []
        month_statistices = {}
        
        shipment_count_chart =(
             Order.objects.filter(
                created__range=(shipment_start_date, shipment_end_date),
                status__in=accepted_statuses,
            )
            .annotate(month=TruncMonth("created"))
            .values("month")
            .annotate(IDs_count=Count("id"))
            .order_by("month")
        )

        for item in monthly_revenue:
            total_commissions += item["total_commissions"] or 0
            total_income += item["total_income"] or 0

        for item in shipment_count_chart:
            month_number = item["month"].month

            # extract the value of month from the date field
            month_statistices["month"] = converted_monthly[month_number]
            month_statistices["shipment_count"] = item["IDs_count"]
            shipments_per_month.append(month_statistices)

        for item in monthly_revenue:

            month_number = item["month"].month
            month_expenses = expenses_by_month.get(month_number, 0)
            monthly_expenses_data.append(
                {
                    "name": converted_monthly[month_number],
                    "total_income": float(item["total_income"] or 0),
                    "total_commissions": float(
                        item["total_commissions"] or 0
                    ),
                    # It must be 'total_expenses' not 'total_delivery_expense'
                    "total_delivery_expense": float(month_expenses),
                    "net_profit": float(
                        (item["total_income"] or 0)
                        - (item["total_commissions"] or 0) - month_expenses
                    ),
                }
            )

        orders_statistics_qs = Order.objects.values("status").annotate(
            count=Count("id")
        )
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

        return {
            "start_date": summary_start_date,
            "end_date": summary_end_date,
            "total_revenue": summary_revenue.get("total_revenue") or 0,
            "total_commissions": summary_revenue.get("total_commissions") or 0,
            "total_expenses": summary_expense,
            "net_profit": (
                (summary_revenue.get("total_revenue") or 0) - (summary_expense or 0)
                - (summary_revenue.get("total_commissions") or 0)
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

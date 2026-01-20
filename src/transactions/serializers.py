from datetime import datetime
from datetime import date, timedelta

from django.db.models import Case, Count, DecimalField, F, Sum, Value, When
from django.db.models.functions import TruncMonth
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from orders.models import Order, OrderStatus
from transactions.models import Expense, TransactionType, UserAccountTransaction
from users.models import UserRole
from users.serializers.user_account_serializers import SingleUserAccountSerializer
from utilities.constant import DEFAULT_START_DATE
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")
        if instance.file and request:
            representation["file"] = request.build_absolute_uri(instance.file.url)
        return representation


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


class SingleUserAccountTransactionSerializer(ModelSerializer):
    user_account = SingleUserAccountSerializer()
    class Meta:
        model = UserAccountTransaction
        fields = [
            "id",
            "user_account",
            "amount",
            "transaction_type",
            "is_rolled_back",
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


class ListExpenseSerializer(ModelSerializer):
    transaction = SingleUserAccountTransactionSerializer()
    class Meta:
        model = Expense
        fields = [
            "id",
            "date",
            "cost",
            "description",
            "transaction",
            "created",
            "modified",
        ]

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

    def _get_multiline_chart_data(self, converted_monthly):
        # for multiline chart
        chart_start_date = datetime.now().date().replace(month=1, day=1)
        monthly_expenses_data = []
        revenues = (
            UserAccountTransaction.objects.filter(
                transaction_type=TransactionType.WITHDRAW,
                is_rolled_back=False,
                user_account__role=UserRole.TRADER,
                order_id__isnull=False,
                created__date__gte=chart_start_date,
            ).annotate(month=TruncMonth("created"))
            .values("month")
            .annotate(IDs_count=Sum("amount"))
            .order_by("month")
        )
        
        for item in revenues:
            monthly_expenses_data.append({
                "name": converted_monthly[item["month"].month],
                "total_income": item["IDs_count"],
            })

        commissions = (
            UserAccountTransaction.objects.filter(
                transaction_type=TransactionType.DEPOSIT,
                is_rolled_back=False,
                user_account__role=UserRole.DRIVER,
                order_id__isnull=False,
                created__date__gte=chart_start_date,
            ).annotate(month=TruncMonth("created"))
            .values("month")
            .annotate(total_commissions=Sum("amount"))
            .order_by("month")
        )

        for item in commissions:
            monthly_expenses_data.append({
                "name": converted_monthly[item["month"].month],
                "total_commissions": item["total_commissions"],
            })
        
        expenses = (
            Expense.objects.filter(
                date__gte=chart_start_date,
            ).annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total_expense=Sum("cost"))
            .order_by("month")
        )

        for item in expenses:
            monthly_expenses_data.append({
                "name": converted_monthly[item["month"].month],
                "total_delivery_expense": item["total_expense"],
            })


        merged = {}

        for item in monthly_expenses_data:
            month = item["name"]

            if month not in merged:
                merged[month] = {
                    "name": month,
                    "total_income": 0.0,
                    "total_commissions": 0.0,
                    "total_delivery_expense": 0.0,
                }

            if "total_income" in item:
                merged[month]["total_income"] += float(item["total_income"])

            if "total_commissions" in item:
                merged[month]["total_commissions"] += float(item["total_commissions"])

            if "total_delivery_expense" in item:
                merged[month]["total_delivery_expense"] += float(item["total_delivery_expense"])


        result = []

        for month_data in merged.values():
            month_data["net_profit"] = (
                month_data["total_income"]
                - month_data["total_commissions"]
                - month_data["total_delivery_expense"]
            )
            result.append(month_data)
        
        return result


    def to_representation(self, instance):
        today = date.today()

        summary_start_date = instance.get("start_date", today.replace(day=1))
        summary_end_date = instance.get("end_date", today)
        summary_end_date = summary_end_date + timedelta(days=1)

        monthly_start_date = instance.get("monthly_start_date", DEFAULT_START_DATE)
        monthly_end_date = instance.get("monthly_end_date", today)
        monthly_end_date = monthly_end_date + timedelta(days=1)

        shipment_start_date = instance.get("shipment_start_date", DEFAULT_START_DATE)
        shipment_end_date = instance.get("shipment_end_date", today)
        shipment_end_date = shipment_end_date + timedelta(days=1)

        converted_monthly = {
            1: "يناير",
            2: "فبراير",
            3: "مارس",
            4: "أبريل",
            5: "مايو",
            6: "يونيو",
            7: "يوليو",
            8: "أغسطس",
            9: "سبتمبر",
            10: "أكتوبر",
            11: "نوفمبر",
            12: "ديسمبر",
        }

        # for shipments chart
        shipment_count_chart = (
            Order.objects.filter(
                created__range=(shipment_start_date, shipment_end_date),
                status__in=[OrderStatus.DELIVERED],
            )
            .annotate(month=TruncMonth("created"))
            .values("month")
            .annotate(IDs_count=Count("id", distinct=True))
            .order_by("month")
        )

        shipments_per_month = []
        for item in shipment_count_chart:
            shipments_per_month.append({
                "month": converted_monthly[item["month"].month],
                "shipment_count": item["IDs_count"],
            })

        # first line
        total_revenue = (
            UserAccountTransaction.objects.filter(
                created__range=(summary_start_date, summary_end_date),
                transaction_type=TransactionType.WITHDRAW,
                is_rolled_back=False,
                user_account__role=UserRole.TRADER,
                order_id__isnull=False,
            ).aggregate(total_revenue=Sum("amount"))["total_revenue"]
            or 0
        )

        total_commissions = (
            UserAccountTransaction.objects.filter(
                created__range=(summary_start_date, summary_end_date),
                transaction_type=TransactionType.DEPOSIT,
                is_rolled_back=False,
                user_account__role=UserRole.DRIVER,
                order_id__isnull=False,
            ).aggregate(total_commissions=Sum("amount"))["total_commissions"]
            or 0
        )
        summary_expense = (
            Expense.objects.filter(
                date__range=(summary_start_date, summary_end_date)
            ).aggregate(total_expense=Sum("cost"))
        )["total_expense"] or 0

        # second line
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

        monthly_expenses_data = self._get_multiline_chart_data(converted_monthly)

        return {
            "date": {
                "summary_start_date": summary_start_date,
                "summary_end_date": summary_end_date,
                "monthly_start_date": monthly_start_date,
                "monthly_end_date": monthly_end_date,
                "shipment_start_date": shipment_start_date,
                "shipment_end_date": shipment_end_date,
            },
            "total_revenue": total_revenue,
            "total_commissions": total_commissions,
            "total_expenses": summary_expense,
            "net_profit": total_revenue - summary_expense - total_commissions,

            "orders": orders_statistics,

            "shipments_per_month": shipments_per_month,
            "monthly_expenses_data": monthly_expenses_data,
        }

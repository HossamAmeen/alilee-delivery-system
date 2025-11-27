from datetime import date

from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.models import Expense, UserAccountTransaction
from transactions.serializers import (
    ExpenseSerializer,
    FinancialInsightsSerializer,
    UserAccountTransactionSerializer,
)
from utilities.api import BaseViewSet


class UserAccountTransactionViewSet(BaseViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = UserAccountTransaction.objects.order_by("-id")
    serializer_class = UserAccountTransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["transaction_type", "user_account"]
    ordering = ["-id"]


class ExpenseViewSet(BaseViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Expense.objects.order_by("-id")
    serializer_class = ExpenseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["date"]
    search_fields = ["description"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(self.paginate_queryset(queryset), many=True)
        # Stats
        yearly_data = (
            Expense.objects.annotate(year=ExtractYear("date"))
            .values("year")
            .annotate(total=Sum("cost"))
            .order_by("year")
        )

        monthly_data = (
            Expense.objects.filter(date__year=date.today().year)
            .annotate(month=ExtractMonth("date"))
            .values("month")
            .annotate(total=Sum("cost"))
            .order_by("month")
        )

        converted_monthly = {
            1: "يناير",
            2: "فبراير",
            3: "مارس",
            4: "ابريل",
            5: "مايو",
            6: "يونيو",
            7: "يوليو",
            8: "اغسطس",
            9: "سبتمبر",
            10: "اكتوبر",
            11: "نوفمبر",
            12: "ديسمبر",
        }

        statistics_data = {
            "total_expenses": Expense.objects.aggregate(total=Sum("cost"))["total"]
            or 0.00,
            "yearly": [
                {"year": item["year"], "total": float(item["total"])}
                for item in yearly_data[:6]
            ],
            "monthly": [
                {
                    "month": converted_monthly[item["month"]],
                    "total": float(item["total"]),
                }
                for item in monthly_data
            ],
        }

        response_data = {"expenses": serializer.data, "statistics": statistics_data}
        return self.get_paginated_response(response_data)


class FinancialInsightsApiView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "start_date": openapi.Schema(type=openapi.TYPE_STRING, example="2025-01-15"),
                    "end_date": openapi.Schema(type=openapi.TYPE_STRING, example="2025-12-02"),
                    "total_revenue": openapi.Schema(type=openapi.TYPE_NUMBER, example=75.0),
                    "total_expenses": openapi.Schema(type=openapi.TYPE_NUMBER, example=250.0),
                    "net_profit": openapi.Schema(type=openapi.TYPE_NUMBER, example=-175.0),
                    "shipments_completed": openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                    "pending_receivables": openapi.Schema(type=openapi.TYPE_NUMBER, example=0.0),
                    "pending_payables": openapi.Schema(type=openapi.TYPE_NUMBER, example=0.0),
                    "balance": openapi.Schema(type=openapi.TYPE_NUMBER, example=-175.0),
                    "monthlyExpensesData": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "name": openapi.Schema(type=openapi.TYPE_STRING, example="Oct"),
                                "total_income": openapi.Schema(type=openapi.TYPE_NUMBER, example=50.0),
                                "total_delivery_expense": openapi.Schema(type=openapi.TYPE_NUMBER, example=100.0),
                                "net_profit": openapi.Schema(type=openapi.TYPE_NUMBER, example=-50.0),
                            },
                        ),
                    ),
                }
            )
        },
        operation_summary="Get financial insights",
        operation_description="Returns revenue, expenses, profit, and monthly breakdown for the selected date range.",
    )
    def get(self, request):
        serializer = FinancialInsightsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

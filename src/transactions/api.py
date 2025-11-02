from datetime import date

from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from transactions.models import Expense, TraderTransaction
from transactions.serializers import ExpenseSerializer, TraderTransactionSerializer
from utilities.api import BaseViewSet


class TraderTransactionViewSet(BaseViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = TraderTransaction.objects.all()
    serializer_class = TraderTransactionSerializer
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

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
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
        return Response(serializer.data)

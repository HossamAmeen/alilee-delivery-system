from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from transactions.models import Expense, TraderTransaction
from transactions.serializers import ExpenseSerializer, TraderTransactionSerializer
from utilities.api import BaseViewSet


class TraderTransactionViewSet(BaseViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = TraderTransaction.objects.all()
    serializer_class = TraderTransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["transaction_type", "user_account"]
    ordering = ["-created"]


class ExpenseViewSet(BaseViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Expense.objects.order_by("-id")
    serializer_class = ExpenseSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "user_account", "expense_date"]
    search_fields = ["description"]

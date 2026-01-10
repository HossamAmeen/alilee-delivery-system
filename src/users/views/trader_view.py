from django.db.models import Count, DecimalField, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from transactions.models import TransactionType
from users.models import Trader
from users.serializers.traders_serializers import (
    RetrieveTraderSerializer,
    TraderListSerializer,
    TraderSerializer,
)
from utilities.api import BaseViewSet


class TraderViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Trader.objects.annotate(
        total_sales=Coalesce(
            Sum(
                "transactions__amount",
                filter=Q(
                    transactions__transaction_type=TransactionType.WITHDRAW,
                    transactions__is_rolled_back=False,
                    transactions__order_id__isnull=False,
                ),
                distinct=True,
            ),
            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
        ),
        orders_count=Coalesce(
            Count("orders", distinct=True), Value(0, output_field=IntegerField())
        ),
    )
    serializer_class = TraderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "email",
        "full_name",
        "phone_number",
        "role",
        "is_active",
        "balance",
        "status",
    ]
    search_fields = ["email", "full_name", "phone_number"]
    ordering_fields = [
        "email",
        "full_name",
        "phone_number",
        "role",
        "balance",
        "status",
    ]
    ordering = ["-id"]

    def get_serializer_class(self):
        if self.action == "list":
            return TraderListSerializer
        if self.action == "retrieve":
            return RetrieveTraderSerializer
        return self.serializer_class

from django.db.models import (
    Count,
    DecimalField,
    IntegerField,
    OuterRef,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from transactions.models import TransactionType, UserAccountTransaction
from users.models import Trader
from users.serializers.traders_serializers import (
    RetrieveTraderSerializer,
    TraderListSerializer,
    TraderSerializer,
)
from utilities.api import BaseViewSet


class TraderViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Trader.objects.order_by("-id")
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

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Trader.objects.none()
        if self.action == "list" or self.action == "retrieve":
            total_sales_subquery = (
                UserAccountTransaction.objects.filter(
                    user_account=OuterRef("pk"),
                    transaction_type=TransactionType.WITHDRAW,
                    is_rolled_back=False,
                    order_id__isnull=False,
                )
                .values("user_account")
                .annotate(total=Sum("amount"))
                .values("total")
            )

            queryset = Trader.objects.annotate(
                total_sales=Coalesce(
                    Subquery(total_sales_subquery, output_field=DecimalField()),
                    Value(0, output_field=DecimalField()),
                ),
                orders_count=Coalesce(
                    Count("orders", distinct=True),
                    Value(0, output_field=IntegerField()),
                ),
            )
            return queryset
        return self.queryset

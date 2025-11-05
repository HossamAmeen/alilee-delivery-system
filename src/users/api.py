from django.db.models import DecimalField, Prefetch, Q, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from trader_pricing.models import TraderDeliveryZone
from transactions.models import TransactionType, UserAccountTransaction
from users.models import Trader, UserAccount
from users.serializers.driver_serializer import (
    CreateUpdateDriverSerializer,
    DriverDetailSerializer,
    ListDriverSerializer,
)
from users.serializers.traders_serializers import TraderListSerializer, TraderSerializer
from users.serializers.user_account_serializers import UserAccountSerializer
from utilities.api import BaseViewSet


class UserAccountViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["email", "full_name", "phone_number", "role"]
    search_fields = ["email", "full_name", "phone_number"]
    ordering_fields = ["email", "full_name", "phone_number", "role"]
    ordering = ["-id"]

    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        request.data.pop("role", None)
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TraderViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Trader.objects.annotate(
        sales=Coalesce(
            Sum(
                "transactions__amount",
                filter=Q(transactions__transaction_type=TransactionType.WITHDRAW),
            ),
            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
        )
    )
    serializer_class = TraderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "email",
        "full_name",
        "phone_number",
        "role",
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
        return self.serializer_class

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "trader_delivery_zones_trader",
                    queryset=TraderDeliveryZone.objects.select_related(
                        "delivery_zone"
                    ).order_by("-id")[:5],
                    to_attr="prefetched_prices",
                ),
                Prefetch(
                    "transactions",
                    queryset=UserAccountTransaction.objects.order_by("-id")[:5],
                    to_attr="prefetched_transactions",
                ),
            )

        return queryset


class DriverViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = UserAccount.objects.filter(role="driver").annotate(
        sales=Coalesce(
            Sum(
                "transactions__amount",
                filter=Q(transactions__transaction_type=TransactionType.WITHDRAW),
            ),
            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
        ),
        order_count=Value(
            0, output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
    )
    serializer_class = UserAccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["email", "full_name", "phone_number"]
    search_fields = ["email", "full_name", "phone_number"]
    ordering_fields = ["email", "full_name", "phone_number"]
    ordering = ["-id"]

    def get_serializer_class(self):
        if self.action == "list":
            return ListDriverSerializer
        elif self.action == "retrieve":
            return DriverDetailSerializer
        else:
            return CreateUpdateDriverSerializer

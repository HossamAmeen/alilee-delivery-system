from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from users.models import UserRole
from utilities.api import BaseViewSet
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order
from .serializers import (
    OrderListSerializer,
    OrderRetrieveSerializer,
    OrderSerializer,
)


class OrderViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "driver",
        "trader",
        "customer",
        "delivery_zone",
        "status",
    ]

    search_fields = [
        "tracking_number",
        "reference_code",
        "customer__full_name",
        "customer__email",
        "customer__phone_number",
        "trader__full_name",
        "trader__email",
        "trader__phone_number",
        "driver__full_name",
        "driver__email",
        "driver__phone_number",
    ]

    ordering_fields = [
        "tracking_number",
        "reference_code",
        "created",
        "modified",
    ]
    ordering = ["-id"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderRetrieveSerializer
        elif self.action == "list":
            return OrderListSerializer
        return self.serializer_class

    def get_queryset(self):
        user = self.request.user

        self.queryset = Order.objects.all().select_related(
            "driver", "trader", "customer", "delivery_zone"
        )

        if user.role == UserRole.DRIVER:
            return self.queryset.filter(driver=user)

        elif user.role == UserRole.TRADER:
            return self.queryset.filter(trader=user)

        return self.queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Prevent update if delivered or cancelled
        if instance.status in ["delivered", "cancelled"]:
            return Response(
                {"detail": "Delivered or cancelled orders cannot be updated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs)

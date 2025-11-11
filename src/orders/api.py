from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404

from users.models import UserRole, Trader
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
        return OrderSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'driver',
                openapi.IN_QUERY,
                description='Filter by driver ID',
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'trader',
                openapi.IN_QUERY,
                description='Filter by trader ID',
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'customer',
                openapi.IN_QUERY,
                description='Filter by customer ID',
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'delivery_zone',
                openapi.IN_QUERY,
                description='Filter by delivery zone ID',
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description='Filter by order status',
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description='Search in tracking number, reference code, or user details',
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description='Which field to use when ordering the results. Prefix with - for descending order.',
                type=openapi.TYPE_STRING,
                enum=['tracking_number', '-tracking_number', 'reference_code', '-reference_code', 'created', '-created', 'modified', '-modified']
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()

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

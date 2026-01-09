from django.db.models import Count, DecimalField, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from notifications.service import send_notification
from orders.models import OrderStatus
from orders.permissions import IsDriverPermission
from transactions.models import TransactionType
from users.models import Driver
from users.serializers.driver_serializer import (
    CreateUpdateDriverSerializer,
    DriverDetailSerializer,
    DriverInsightsSerializer,
    DriverTokenObtainPairSerializer,
    DriverTokenRefreshSerializer,
    ListDriverSerializer,
)
from users.serializers.user_account_serializers import UserAccountSerializer
from utilities.api import BaseViewSet


class DriverViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Driver.objects.filter().order_by("-id")
    serializer_class = UserAccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["email", "full_name", "phone_number", "is_active"]
    search_fields = ["email", "full_name", "phone_number"]
    ordering_fields = ["email", "full_name", "phone_number"]
    ordering = ["-id"]

    def get_queryset(self):
        qs = super().get_queryset()
        # for filter orders by date
        date = self.request.query_params.get("date")
        order_filter = Q()
        sales_filter = Q(transactions__transaction_type=TransactionType.WITHDRAW)
        if date:
            order_filter = Q(orders__created__date=date)
            sales_filter &= Q(transactions__created__date=date)
            pass

        # annotate sales from wallet transactions (withdrawals) and order totals
        delivered_filter = order_filter & Q(
            orders__status__in=[OrderStatus.DELIVERED, OrderStatus.CANCELLED]
        )

        qs = qs.annotate(
            total_delivery_cost=Coalesce(
                Sum(
                    "",
                    filter=delivered_filter,
                ),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
            ),
            total_extra_delivery_cost=Coalesce(
                Sum(
                    "orders__extra_delivery_cost",
                    filter=delivered_filter,
                ),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
            ),
            order_count=Coalesce(
                Count(
                    "orders",
                    filter=order_filter,
                ),
                Value(0, output_field=IntegerField()),
            ),
        )

        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ListDriverSerializer
        elif self.action == "retrieve":
            return DriverDetailSerializer
        else:
            return CreateUpdateDriverSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_status = instance.is_active
        self.perform_update(serializer)
        if old_status != instance.is_active:
            message = "تم تنشيط حسابك" if instance.is_active else "تم تعطيل حسابك"
            send_notification(
                instance.id,
                "تعديل حالة حسابك",
                message,
            )
        return Response(serializer.data)

    def profile(self, request):
        # enforce driver permission
        perm = IsDriverPermission()
        if not perm.has_permission(request, self):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = CreateUpdateDriverSerializer(request.user)
        return Response(serializer.data)

    def update_profile(self, request):
        serializer = CreateUpdateDriverSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DriverInsightsAPIView(APIView):
    permission_classes = (IsAuthenticated, IsDriverPermission)
    serializer_class = DriverInsightsSerializer

    @swagger_auto_schema(
        operation_description="Get insights for the authenticated driver",
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date to filter prices (YYYY-MM-DD). If not provided, all prices are returned.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date to filter prices (YYYY-MM-DD). If not provided, all prices are returned.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "total_deliveries": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Number of delivered orders",
                    ),
                    "assigned_order_count": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Number of assigned orders",
                    ),
                    "total_earnings": openapi.Schema(
                        type=openapi.TYPE_NUMBER,
                        description="Total earnings from delivered orders",
                    ),
                    "delivered": openapi.Schema(
                        type=openapi.TYPE_INTEGER, description="Delivered orders count"
                    ),
                    "pending": openapi.Schema(
                        type=openapi.TYPE_INTEGER, description="Pending orders count"
                    ),
                    "canceled": openapi.Schema(
                        type=openapi.TYPE_INTEGER, description="Canceled orders count"
                    ),
                    "in_progress": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Orders in progress count",
                    ),
                },
            )
        },
    )
    def get(self, request):
        serializer = DriverInsightsSerializer(
            request.user, context=request.query_params
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class DriverTokenObtainPairView(TokenObtainPairView):
    serializer_class = DriverTokenObtainPairSerializer


class DriverTokenRefreshView(TokenRefreshView):
    serializer_class = DriverTokenRefreshSerializer

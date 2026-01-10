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

from transactions.models import TransactionType
from users.models import Trader, UserAccount
from users.serializers.traders_serializers import (
    RetrieveTraderSerializer,
    TraderListSerializer,
    TraderSerializer,
)
from users.serializers.user_account_serializers import (
    FirebaseDeviceSerializer,
    UserAccountSerializer,
)
from utilities.api import BaseViewSet

from .models import FirebaseDevice


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

    @swagger_auto_schema(
        operation_description="Retrieve a trader by ID, with optional date parameter to filter prices.",
        manual_parameters=[
            openapi.Parameter(
                "date",
                openapi.IN_QUERY,
                description="Date to filter prices (YYYY-MM-DD). If not provided, all prices are returned.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            )
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            context={
                "date": request.query_params.get("date"),
                "request": request,
            },
        )
        return Response(serializer.data)


class FirebaseDeviceRegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=FirebaseDeviceSerializer)
    def post(self, request):
        serializer = FirebaseDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        user = request.user

        device, created = FirebaseDevice.objects.get_or_create(
            token=token,
            defaults={"user": user},
        )

        if not created and device.user != user:
            device.user = user
            device.save(update_fields=["user", "last_seen"])

        return Response(
            {
                "created": created,
                "token": device.token,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @swagger_auto_schema(request_body=FirebaseDeviceSerializer)
    def delete(self, request):
        serializer = FirebaseDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        FirebaseDevice.objects.filter(user=request.user, token=token).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

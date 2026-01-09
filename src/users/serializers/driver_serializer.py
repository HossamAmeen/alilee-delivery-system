from datetime import date, timedelta

from django.db.models import Count, Q, Sum
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken

from orders.models import Order, OrderStatus
from transactions.serializers import UserAccountTransactionSerializer
from users.models import Driver, UserRole
from utilities.constant import DEFAULT_START_DATE
from utilities.exceptions import CustomValidationError


class ListDriverSerializer(serializers.ModelSerializer):
    sales = serializers.SerializerMethodField()
    order_count = serializers.IntegerField()

    class Meta:
        model = Driver
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "balance",
            "vehicle_number",
            "license_number",
            "sales",
            "order_count",
            "is_active",
            "date_joined",
        ]

    def get_sales(self, obj):
        # Use annotated values when available; fall back to 0
        total = (getattr(obj, "total_delivery_cost", None) or 0) + (
            getattr(obj, "total_extra_delivery_cost", None) or 0
        )
        return total


class SingleDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "is_active",
        ]


class RetrieveDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "vehicle_number",
            "license_number",
            "is_active",
            "date_joined",
        ]


class CreateUpdateDriverSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(
        write_only=True, required=True, min_length=8
    )

    class Meta:
        model = Driver
        fields = [
            "email",
            "full_name",
            "phone_number",
            "vehicle_number",
            "license_number",
            "is_active",
            "password",
            "confirm_password",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, data):
        # Check that password and confirm_password match
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password != confirm_password:
            raise CustomValidationError({"confirm_password": "Passwords do not match."})

        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password", None)
        driver = Driver(**validated_data)
        if password:
            driver.set_password(password)
        driver.save()
        return driver

    def update(self, instance, validated_data):
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class DriverDetailSerializer(serializers.ModelSerializer):
    sales = serializers.SerializerMethodField()
    order_count = serializers.IntegerField()
    orders = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()
    total_delivery_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_extra_delivery_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2
    )

    class Meta:
        model = Driver
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "vehicle_number",
            "license_number",
            "is_active",
            "date_joined",
            "sales",
            "order_count",
            "total_delivery_cost",
            "total_extra_delivery_cost",
            "orders",
            "transactions",
        ]

    def get_orders(self, obj):
        from orders.serializers import SingleOrderSerializer

        return SingleOrderSerializer(obj.orders.order_by("-id")[:3], many=True).data

    def get_transactions(self, obj):
        qs = obj.transactions.order_by("-id")[:3]
        return UserAccountTransactionSerializer(
            qs, many=True, context={"request": self.context.get("request")}
        ).data

    def get_sales(self, obj):
        # Use annotated values when available; fall back to 0
        total = (getattr(obj, "total_delivery_cost", None) or 0) + (
            getattr(obj, "total_extra_delivery_cost", None) or 0
        )
        return total


class DriverInsightsSerializer(serializers.Serializer):
    driver = serializers.PrimaryKeyRelatedField(
        queryset=Driver.objects.all(), required=True
    )

    def to_representation(self, instance):
        start_date = self.context.get("start_date", DEFAULT_START_DATE)
        end_date = self.context.get("end_date", date.today())
        end_date = end_date + timedelta(days=1)
        aggregates = Order.objects.filter(
            driver=instance, created__range=(start_date, end_date)
        ).aggregate(
            total_delivery_cost=Sum(
                "delivery_cost", filter=Q(status=OrderStatus.DELIVERED)
            ),
            total_extra_delivery_cost=Sum(
                "extra_delivery_cost", filter=Q(status=OrderStatus.DELIVERED)
            ),
            delivered_order_count=Count("id", filter=Q(status=OrderStatus.DELIVERED)),
            assigned_order_count=Count("id", filter=Q(status=OrderStatus.ASSIGNED)),
            pending=Count("id", filter=Q(status=OrderStatus.POSTPONED)),
            canceled=Count("id", filter=Q(status=OrderStatus.CANCELLED)),
            in_progress=Count("id", filter=Q(status=OrderStatus.IN_PROGRESS)),
        )

        total_earnings = (aggregates["total_delivery_cost"] or 0) + (
            aggregates["total_extra_delivery_cost"] or 0
        )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "balance": instance.driver.balance,
            "total_earnings": total_earnings,
            "delivered_order_count": aggregates["delivered_order_count"],
            "delivered": aggregates["delivered_order_count"],
            "assigned_order_count": aggregates["assigned_order_count"],
            "pending": aggregates["pending"],
            "canceled": aggregates["canceled"],
            "in_progress": aggregates["in_progress"],
        }


class DriverTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = getattr(self, "user", None)
        if user is None or user.role != UserRole.DRIVER:
            raise CustomValidationError(
                message="No active account found with the given credentials"
            )
        return data


class DriverTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = attrs.get("refresh")
        try:
            token = RefreshToken(refresh)
        except Exception as exc:
            raise exceptions.AuthenticationFailed("Invalid refresh token") from exc

        role = token.get("role", None)
        if role != UserRole.DRIVER:
            raise exceptions.AuthenticationFailed(
                "Refresh token does not belong to a driver", code="authorization"
            )

        return super().validate(attrs)

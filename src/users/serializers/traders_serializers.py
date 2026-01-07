from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from transactions.serializers import UserAccountTransactionSerializer
from users.models import Trader, UserRole


class TraderSerializer(ModelSerializer):
    class Meta:
        model = Trader
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "is_active",
            "created",
            "modified",
        ]
        read_only_fields = ("id", "created", "modified")

    def create(self, validated_data):
        validated_data["role"] = UserRole.TRADER
        return super().create(validated_data)


class TraderListSerializer(serializers.ModelSerializer):
    total_sales = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    orders_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Trader
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "is_active",
            "total_sales",
            "orders_count",
            "created",
            "modified",
        ]
        read_only_fields = ("id", "created", "modified")


class SingleTraderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trader
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "is_active",
        ]


class RetrieveTraderSerializer(serializers.ModelSerializer):
    total_sales = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    orders_count = serializers.IntegerField(read_only=True)
    prices = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()

    class Meta:
        model = Trader
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "is_active",
            "total_sales",
            "orders_count",
            "prices",
            "transactions",
            "orders",
        ]

    def get_prices(self, obj):
        from trader_pricing.serializers import TraderDeliveryZoneNestedSerializer

        qs = obj.trader_delivery_zones_trader.order_by("-id")
        return TraderDeliveryZoneNestedSerializer(qs[:3], many=True).data

    def get_transactions(self, obj):
        qs = obj.transactions.order_by("-id")[:3]
        return UserAccountTransactionSerializer(
            qs, many=True, context={"request": self.context.get("request")}
        ).data

    def get_orders(self, obj):
        from orders.serializers import OrderTraderSerializer

        qs = obj.orders.order_by("-id")[:3]
        return OrderTraderSerializer(qs, many=True).data

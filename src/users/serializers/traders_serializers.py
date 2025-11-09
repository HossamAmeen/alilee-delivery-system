from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from trader_pricing.serializers import TraderDeliveryZoneNestedSerializer
from transactions.serializers import UserAccountTransactionSerializer
from users.models import Trader, UserRole


class TraderSerializer(ModelSerializer):
    prices = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()
    sales = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Trader
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "created",
            "modified",
            "prices",
            "sales",
            "transactions",
            "orders",
        ]
        read_only_fields = ("id", "created", "modified")

    def create(self, validated_data):
        validated_data["role"] = UserRole.TRADER
        return super().create(validated_data)

    def get_prices(self, obj):
        qs = obj.trader_delivery_zones_trader.order_by("-id")[:5]
        return TraderDeliveryZoneNestedSerializer(qs, many=True).data

    def get_transactions(self, obj):
        qs = obj.transactions.order_by("-id")[:5]
        return UserAccountTransactionSerializer(qs, many=True).data

    def get_orders(self, obj):
        from orders.serializers import OrderTraderSerializer

        qs = obj.orders.order_by("-id")[:5]
        return OrderTraderSerializer(qs, many=True).data


class TraderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trader
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "status",
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
            "status",
        ]


class RetrieveTraderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trader
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "status",
        ]

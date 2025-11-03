from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from trader_pricing.serializers import TraderDeliveryZoneNestedSerializer
from users.models import Trader, UserRole


class TraderSerializer(ModelSerializer):
    prices = TraderDeliveryZoneNestedSerializer(
        source="trader_delivery_zones_trader",
        many=True,
        read_only=True
    )
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
        ]
        read_only_fields = ("id", "created", "modified")

    def create(self, validated_data):
        validated_data["role"] = UserRole.TRADER
        return super().create(validated_data)


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

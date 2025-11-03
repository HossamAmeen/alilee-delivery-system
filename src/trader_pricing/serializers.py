from rest_framework import serializers

from trader_pricing.models import TraderDeliveryZone


class TraderDeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraderDeliveryZone
        fields = ["price", "trader", "delivery_zone"]


class TraderDeliveryZoneNestedSerializer(serializers.ModelSerializer):
    delivery_zone = serializers.CharField(source="delivery_zone.name", read_only=True)

    class Meta:
        model = TraderDeliveryZone
        fields = ["price", "delivery_zone"]

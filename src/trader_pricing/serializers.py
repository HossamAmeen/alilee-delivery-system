from rest_framework import serializers

from trader_pricing.models import TraderDeliveryZone
from geo.serializers import SingleDeliveryZoneSerializer
from users.serializers.traders_serializers import SingleTraderSerializer


class TraderDeliveryZoneSerializer(serializers.ModelSerializer):
    trader = SingleTraderSerializer()
    delivery_zone = SingleDeliveryZoneSerializer()
    class Meta:
        model = TraderDeliveryZone
        fields = ["price", "trader", "delivery_zone"]


class TraderDeliveryZoneNestedSerializer(serializers.ModelSerializer):
    delivery_zone = serializers.CharField(source="delivery_zone.name", read_only=True)

    class Meta:
        model = TraderDeliveryZone
        fields = ["id", "price", "delivery_zone"]

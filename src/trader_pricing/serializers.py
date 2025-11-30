from rest_framework import serializers

from geo.serializers import SingleDeliveryZoneSerializer
from trader_pricing.models import TraderDeliveryZone
from users.serializers.traders_serializers import SingleTraderSerializer


class ListTraderDeliveryZoneSerializer(serializers.ModelSerializer):
    trader = SingleTraderSerializer()
    delivery_zone = SingleDeliveryZoneSerializer()

    class Meta:
        model = TraderDeliveryZone
        fields = ["id", "price", "trader", "delivery_zone"]


class TraderDeliveryZoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = TraderDeliveryZone
        fields = ["id", "price", "trader", "delivery_zone"]


class TraderDeliveryZoneNestedSerializer(serializers.ModelSerializer):
    delivery_zone = serializers.CharField(source="delivery_zone.name", read_only=True)

    class Meta:
        model = TraderDeliveryZone
        fields = ["id", "price", "delivery_zone"]

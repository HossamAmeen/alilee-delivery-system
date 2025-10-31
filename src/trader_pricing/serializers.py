from rest_framework import serializers

from trader_pricing.models import TraderDeliveryZone


class TraderDeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraderDeliveryZone
        fields = ["price", "trader", "delivery_zone"]

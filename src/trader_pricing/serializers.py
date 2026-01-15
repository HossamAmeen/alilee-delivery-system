from rest_framework import serializers

from geo.serializers import SingleDeliveryZoneSerializer
from trader_pricing.models import TraderDeliveryZone
from users.serializers.traders_serializers import SingleTraderSerializer
from utilities.exceptions import CustomValidationError


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
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=TraderDeliveryZone.objects.all(),
                fields=["delivery_zone", "trader"],
                message="هذا التاجر لديه بالفعل تسعيرة لهذه المنطقة",
            )
        ]

    def validate(self, attrs):
        trader = attrs.get("trader")
        delivery_zone = attrs.get("delivery_zone")

        # Check if the combination already exists
        queryset = TraderDeliveryZone.objects.filter(
            trader=trader, delivery_zone=delivery_zone
        )
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise CustomValidationError(
                {"message": "هذا التاجر لدية بالفعل تسعيرة لهذه المنطقة"}
            )

        return attrs


class TraderDeliveryZoneNestedSerializer(serializers.ModelSerializer):
    delivery_zone = serializers.CharField(source="delivery_zone.name", read_only=True)

    class Meta:
        model = TraderDeliveryZone
        fields = ["id", "price", "delivery_zone"]

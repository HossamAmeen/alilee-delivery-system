from rest_framework import serializers

from geo.models import City, DeliveryZone


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name"]


class DeliveryZoneSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)

    class Meta:
        model = DeliveryZone
        fields = ["id", "name", "cost", "city"]


class SingleDeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = ["id", "name", "cost", "city"]

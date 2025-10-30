from rest_framework import serializers

from geo.models import City, DeliveryZone


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name"]


class DeliveryZoneSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)

    class Meta:
        model = DeliveryZone
        fields = ["id", "name", "cost", "city"]

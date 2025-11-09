from django.db.transaction import atomic
from rest_framework import serializers

from geo.serializers import SingleDeliveryZoneSerializer
from users.serializers.driver_serializer import SingleDriverSerializer
from users.serializers.traders_serializers import SingleTraderSerializer, RetrieveTraderSerializer

from .models import Customer, Order


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "address", "location", "phone", "created", "modified"]


class SingleCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "address", "location"]


class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "reference_code",
            "product_cost",
            "extra_delivery_cost",
            "status",
            "payment_method",
            "note",
            "driver",
            "trader",
            "created",
            "modified",
            "customer",
            "delivery_zone",
        ]
        read_only_fields = ("id", "tracking_number", "created", "modified")
        extra_kwargs = {
            "delivery_zone": {"required": True},
            "customer": {"required": True},
            "trader": {"required": True},
        }

    @atomic
    def create(self, validated_data):
        customer_serializer = CustomerSerializer(data=validated_data["customer"])
        customer_serializer.is_valid(raise_exception=True)
        customer = customer_serializer.save()
        validated_data["customer"] = customer
        validated_data["delivery_cost"] = validated_data["delivery_zone"].cost
        return super().create(validated_data)


class OrderRetrieveSerializer(serializers.ModelSerializer):
    driver = SingleDriverSerializer(read_only=True)
    trader = RetrieveTraderSerializer(read_only=True)
    customer = SingleCustomerSerializer(read_only=True)
    delivery_zone = SingleDeliveryZoneSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "reference_code",
            "product_cost",
            "delivery_cost",
            "extra_delivery_cost",
            "total_cost",
            "status",
            "driver",
            "trader",
            "delivery_zone",
            "payment_method",
            "customer",
            "note",
            "created",
            "modified",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    driver = SingleDriverSerializer(read_only=True)
    trader = SingleTraderSerializer(read_only=True)
    customer = SingleCustomerSerializer(read_only=True)
    delivery_zone = SingleDeliveryZoneSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "reference_code",
            "total_cost",
            "status",
            "driver",
            "trader",
            "customer",
            "delivery_zone",
            "created",
        ]


class SingleOrderSerializer(serializers.ModelSerializer):
    trader = SingleTraderSerializer(read_only=True)
    customer = SingleCustomerSerializer(read_only=True)
    delivery_zone = SingleDeliveryZoneSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "reference_code",
            "product_cost",
            "delivery_cost",
            "extra_delivery_cost",
            "total_cost",
            "status",
            "driver",
            "trader",
            "delivery_zone",
            "payment_method",
            "customer",
            "note",
            "created",
            "modified",
        ]


class OrderTraderSerializer(serializers.ModelSerializer):
    customer = SingleCustomerSerializer(read_only=True)
    driver = SingleDriverSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "product_cost",
            "status",
            "driver",
            "customer",
            "created",
        ]

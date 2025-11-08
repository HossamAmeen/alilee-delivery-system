from django.db.transaction import atomic
from rest_framework import serializers

from users.serializers.driver_serializer import RetrieveDriverSerializer
from users.serializers.traders_serializers import TraderListSerializer
from .models import Order, Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "address", "location", "phone", "created", "modified"]


class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "code",
            "subtotal",
            "total_cost",
            "delivery_cost",
            "extra_cost",
            "status",
            "driver",
            "trader",
            "payment_method",
            "note",
            "created",
            "modified",
            "customer",
        ]
        read_only_fields = ("id", "tracking_number", "created", "modified")

    @atomic
    def create(self, validated_data):
        customer = CustomerSerializer(data=validated_data["customer"])
        customer.is_valid(raise_exception=True)
        customer.save()
        validated_data["customer"] = Customer.objects.get(pk=customer.data["id"])
        return super().create(validated_data)


class OrderRetrieveSerializer(serializers.ModelSerializer):
    driver = RetrieveDriverSerializer(read_only=True)
    trader = TraderListSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "code",
            "subtotal",
            "total_cost",
            "delivery_cost",
            "extra_cost",
            "status",
            "driver",
            "trader",
            "payment_method",
            "customer",
            "note",
            "created",
            "modified",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source="driver.full_name", read_only=True)
    trader_name = serializers.CharField(source="trader.full_name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "code",
            "status",
            "total_cost",
            "driver_name",
            "trader_name",
            "customer_name",
            "created",
        ]

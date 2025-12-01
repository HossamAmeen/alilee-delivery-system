from django.db.transaction import atomic
from rest_framework import serializers

from geo.serializers import SingleDeliveryZoneSerializer
from users.serializers.driver_serializer import SingleDriverSerializer
from users.serializers.traders_serializers import SingleTraderSerializer
from utilities.exceptions import CustomValidationError

from .models import Customer, Order


class CustomerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Customer
        fields = ["id", "name", "address", "location", "phone", "created", "modified"]


class SingleCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "address", "location"]


class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    product_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    extra_delivery_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    status_ar = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "reference_code",
            "product_cost",
            "extra_delivery_cost",
            "status",
            "status_ar",
            "payment_method",
            "product_payment_status",
            "note",
            "longitude",
            "latitude",
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
        merchant_cost = (
            validated_data["trader"]
            .trader_delivery_zones_trader.filter(
                delivery_zone=validated_data["delivery_zone"]
            )
            .first()
        )
        if not merchant_cost:
            raise CustomValidationError(
                "The selected trader does not serve the selected delivery zone."
            )

        validated_data["trader_merchant_cost"] = merchant_cost.price
        return super().create(validated_data)

    @atomic
    def update(self, instance, validated_data):
        if validated_data.get("customer"):
            if not validated_data["customer"].get("id"):
                raise CustomValidationError("Customer ID is required")
            customer_serializer = CustomerSerializer(
                instance.customer, data=validated_data["customer"], partial=True
            )
            customer_serializer.is_valid(raise_exception=True)
            customer = customer_serializer.save()
            validated_data["customer"] = customer

        if (
            validated_data.get("delivery_zone")
            and validated_data["delivery_zone"] != instance.delivery_zone_id
        ):
            merchant_cost = (
                validated_data.get("trader", instance.trader)
                .trader_delivery_zones_trader.filter(
                    delivery_zone=validated_data["delivery_zone"]
                )
                .first()
            )
            if not merchant_cost:
                raise CustomValidationError(
                    "The selected trader does not serve the selected delivery zone."
                )
        return super().update(instance, validated_data)


class OrderRetrieveSerializer(serializers.ModelSerializer):
    driver = SingleDriverSerializer(read_only=True)
    trader = SingleTraderSerializer(read_only=True)
    customer = SingleCustomerSerializer(read_only=True)
    delivery_zone = SingleDeliveryZoneSerializer(read_only=True)
    status_ar = serializers.CharField(read_only=True)

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
            "trader_merchant_cost",
            "status",
            "status_ar",
            "driver",
            "trader",
            "delivery_zone",
            "payment_method",
            "product_payment_status",
            "longitude",
            "latitude",
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
    status_ar = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "reference_code",
            "total_cost",
            "status",
            "status_ar",
            "driver",
            "trader",
            "customer",
            "delivery_zone",
            "created",
            "longitude",
            "latitude",
        ]


class SingleOrderSerializer(serializers.ModelSerializer):
    trader = SingleTraderSerializer(read_only=True)
    customer = SingleCustomerSerializer(read_only=True)
    delivery_zone = SingleDeliveryZoneSerializer(read_only=True)
    status_ar = serializers.CharField(read_only=True)

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
            "status_ar",
            "driver",
            "trader",
            "delivery_zone",
            "payment_method",
            "product_payment_status",
            "customer",
            "note",
            "longitude",
            "latitude",
            "created",
            "modified",
        ]


class OrderTraderSerializer(serializers.ModelSerializer):
    customer = SingleCustomerSerializer(read_only=True)
    driver = SingleDriverSerializer(read_only=True)
    status_ar = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "product_cost",
            "status",
            "status_ar",
            "driver",
            "customer",
            "created",
            "longitude",
            "latitude",
        ]


class OrderTrackingNumberSerializer(serializers.ModelSerializer):
    driver = serializers.IntegerField()
    tracking_numbers = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Order
        fields = ["tracking_numbers", "driver"]

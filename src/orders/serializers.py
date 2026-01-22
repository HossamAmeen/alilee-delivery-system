from django.db.transaction import atomic
from rest_framework import serializers

from geo.serializers import SingleDeliveryZoneSerializer
from notifications.service import send_notification
from orders.models import Customer, Order, OrderStatus
from users.models import Driver, Trader
from users.serializers.driver_serializer import SingleDriverSerializer
from users.serializers.traders_serializers import SingleTraderSerializer
from utilities.exceptions import CustomValidationError


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
            "cancel_reason",
            "postpone_reason",
            "trader_cost",
            "trader_merchant_cost",
            "is_return",
            "image",
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
        validated_data["trader_cost"] = merchant_cost.price
        return super().create(validated_data)

    @atomic
    def update(self, instance, validated_data):
        is_new_changes = False
        if instance.status in [
            OrderStatus.DELIVERED,
            OrderStatus.POSTPONED,
            OrderStatus.CANCELLED,
        ]:
            if instance.status == validated_data.get("status", instance.status):
                raise CustomValidationError("Status cannot be changed for this order.")
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
            validated_data["trader_merchant_cost"] = merchant_cost.price

            validated_data["trader_cost"] = merchant_cost.price
        if not instance.driver and validated_data.get("driver"):
            instance.status = OrderStatus.ASSIGNED
            send_notification(
                title="تم تعيينك كسائق للطلب رقم " + instance.tracking_number,
                description="تم تعيينك كسائق للطلب رقم " + instance.tracking_number,
                user_id=validated_data.get("driver").id,
            )

        if validated_data.get("status") == OrderStatus.CREATED:
            instance.driver = None

        # if the order is updated
        if (
            validated_data.get("status") != instance.status
            or validated_data.get("driver") != instance.driver
            or validated_data.get("trader") != instance.trader
            or validated_data.get("delivery_zone") != instance.delivery_zone
            or validated_data.get("product_cost") != instance.product_cost
            or validated_data.get("extra_delivery_cost") != instance.extra_delivery_cost
            or validated_data.get("note") != instance.note
            or validated_data.get("is_return") != instance.is_return
        ):
            is_new_changes = True

        customer_data = validated_data.get("customer")
        if customer_data:
            if (
                customer_data.phone != instance.customer.phone
                or customer_data.name != instance.customer.name
                or customer_data.address != instance.customer.address
            ):
                is_new_changes = True

        if is_new_changes and instance.driver:
            send_notification(
                title="تم تعديل بيانات الشحنه الرجاء التحقق من الشحنه رقم "
                + instance.tracking_number,
                description="تم تعديل بيانات الشحنه الرجاء التحقق من الشحنه رقم "
                + instance.tracking_number,
                user_id=instance.driver.id,
            )

        return super().update(instance, validated_data)

    def validate(self, data):
        trader = Trader.objects.filter(pk=data.get("trader"), is_active=True).first()
        if data.get("trader") and not trader:
            raise CustomValidationError(message="Trader is not active or not found")

        driver = Driver.objects.filter(pk=data.get("driver"), is_active=True).first()
        if data.get("driver") and not driver:
            raise CustomValidationError(message="Driver is not active or not found")

        return data


class OrderRetrieveSerializer(serializers.ModelSerializer):
    driver = SingleDriverSerializer(read_only=True)
    trader = SingleTraderSerializer(read_only=True)
    customer = SingleCustomerSerializer(read_only=True)
    delivery_zone = SingleDeliveryZoneSerializer(read_only=True)
    status_ar = serializers.CharField(read_only=True)
    total_cost = serializers.SerializerMethodField()

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
            "trader_cost",
            "trader_merchant_cost",
            "status",
            "status_ar",
            "driver",
            "trader",
            "delivery_zone",
            "product_payment_status",
            "longitude",
            "latitude",
            "customer",
            "note",
            "created",
            "modified",
            "cancel_reason",
            "postpone_reason",
            "is_return",
            "image",
        ]

    def get_total_cost(self, obj):
        return obj.total_cost_for_driver


class OrderListSerializer(serializers.ModelSerializer):
    driver = SingleDriverSerializer(read_only=True)
    trader = SingleTraderSerializer(read_only=True)
    customer = SingleCustomerSerializer(read_only=True)
    delivery_zone = SingleDeliveryZoneSerializer(read_only=True)
    status_ar = serializers.CharField(read_only=True)
    total_cost = serializers.SerializerMethodField()

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
            "image",
        ]

    def get_total_cost(self, obj):
        return obj.total_cost_for_driver


class SingleOrderSerializer(serializers.ModelSerializer):
    trader = SingleTraderSerializer(read_only=True)
    customer = SingleCustomerSerializer(read_only=True)
    delivery_zone = SingleDeliveryZoneSerializer(read_only=True)
    status_ar = serializers.CharField(read_only=True)
    total_cost = serializers.SerializerMethodField()

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
            "product_payment_status",
            "customer",
            "note",
            "longitude",
            "latitude",
            "created",
            "modified",
            "cancel_reason",
            "postpone_reason",
            "trader_cost",
            "trader_merchant_cost",
            "is_return",
            "image",
        ]

    def get_total_cost(self, obj):
        return obj.total_cost_for_driver


class OrderTraderSerializer(serializers.ModelSerializer):
    customer = SingleCustomerSerializer(read_only=True)
    driver = SingleDriverSerializer(read_only=True)
    status_ar = serializers.CharField(read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "tracking_number",
            "product_cost",
            "total_cost",
            "status",
            "status_ar",
            "driver",
            "customer",
            "created",
            "longitude",
            "latitude",
            "is_return",
            "image",
        ]

    def get_total_cost(self, obj):
        return obj.total_cost_for_driver


class ReferenceCodeSerializer(serializers.Serializer):
    reference_codes = serializers.ListField(child=serializers.CharField())


class OrderTrackingNumberSerializer(serializers.ModelSerializer):
    driver = serializers.IntegerField()
    tracking_numbers = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Order
        fields = ["tracking_numbers", "driver"]

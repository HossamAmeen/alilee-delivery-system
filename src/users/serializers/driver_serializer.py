from django.db.models import Sum
from rest_framework import serializers

from orders.models import Order
from transactions.serializers import UserAccountTransactionSerializer
from users.models import Driver


class ListDriverSerializer(serializers.ModelSerializer):
    sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    order_count = serializers.IntegerField()

    class Meta:
        model = Driver
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "vehicle_number",
            "license_number",
            "sales",
            "order_count",
            "is_active",
            "date_joined",
        ]


class SingleDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "is_active",
        ]


class RetrieveDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "vehicle_number",
            "license_number",
            "is_active",
            "date_joined",
        ]


class CreateUpdateDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "email",
            "full_name",
            "phone_number",
            "vehicle_number",
            "license_number",
            "is_active",
            "password",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        driver = Driver(**validated_data)
        if password:
            driver.set_password(password)
        driver.save()
        return driver

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class DriverDetailSerializer(serializers.ModelSerializer):
    sales = serializers.DecimalField(max_digits=10, decimal_places=2)
    order_count = serializers.IntegerField()
    orders = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "vehicle_number",
            "license_number",
            "is_active",
            "date_joined",
            "sales",
            "order_count",
            "orders",
            "transactions",
        ]

    def get_orders(self, obj):
        from orders.serializers import SingleOrderSerializer

        return SingleOrderSerializer(obj.orders.order_by("-id")[:3], many=True).data

    def get_transactions(self, obj):
        qs = obj.transactions.order_by("-id")[:3]
        return UserAccountTransactionSerializer(qs, many=True).data


class DriverInsightsSerializer(serializers.Serializer):
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.all(),
                                                required=True)

    def to_representation(self, instance):
        driver_orders = Order.objects.filter(driver=instance)
        total_orders = driver_orders.filter(status='DELIVERED').aggregate(
            total_delivery_cost=Sum('delivery_cost'),
            total_extra_delivery_cost=Sum('extra_delivery_cost')
        )
        total_driver_earnings = (total_orders['total_delivery_cost'] or 0) + (
            total_orders['total_extra_delivery_cost'] or 0)

        return {'total_deliveries': driver_orders.filter(status='DELIVERED').count(),
                'shipments': driver_orders.filter(status='ASSIGNED').count(),
                'total_earnings': total_driver_earnings,
                'delivered': driver_orders.filter(status='DELIVERED').count(),
                'pending': driver_orders.filter(status='PENDING').count(),
                'canceled': driver_orders.filter(status='CANCELED').count(),
                'in_porgress': driver_orders.filter(status='IN_PROGRESS').count()
                }

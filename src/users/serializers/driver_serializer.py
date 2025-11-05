from rest_framework import serializers

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
    class Meta:
        model = Driver
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "vehicle_number",
            "license_number",
            "is_active",
            "date_joined",
        ]

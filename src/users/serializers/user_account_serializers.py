from rest_framework import serializers

from users.models import UserAccount
from utilities.exceptions import CustomValidationError


class UserAccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(
        write_only=True, required=True, min_length=8
    )

    class Meta:
        model = UserAccount
        fields = [
            "id",
            "email",
            "password",
            "confirm_password",
            "full_name",
            "phone_number",
            "role",
            "is_active",
            "created",
            "modified",
        ]
        read_only_fields = ("id", "created", "modified")

    def validate(self, data):
        # Check that password and confirm_password match
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password != confirm_password:
            raise CustomValidationError({"confirm_password": "Passwords do not match."})

        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password", None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

from users.models import UserRole
from rest_framework import exceptions, serializers

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


class SingleUserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "role",
            "is_active",
            "created",
            "modified",
        ]


class FirebaseDeviceSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh = attrs.get("refresh")
        try:
            token = RefreshToken(refresh)
        except Exception as exc:
            raise exceptions.AuthenticationFailed("Invalid refresh token") from exc

        role = token.get("role", None)
        if role not in [UserRole.OWNER, UserRole.MANAGER]:
            raise exceptions.AuthenticationFailed(
                "Refresh token does not belong to a owner or manager", code="authorization"
            )

        return super().validate(attrs)

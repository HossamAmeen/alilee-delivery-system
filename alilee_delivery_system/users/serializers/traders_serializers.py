from rest_framework.serializers import ModelSerializer

from users.models import Trader, UserRole


class TraderSerializer(ModelSerializer):
    class Meta:
        model = Trader
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "balance",
            "created",
            "modified",
        ]
        read_only_fields = ("id", "created", "modified", "deleted_at")

    def create(self, validated_data):
        validated_data["role"] = UserRole.TRADER
        return super().create(validated_data)

from rest_framework.serializers import ModelSerializer

from users.models import Trader, UserRole


class TraderSerializer(ModelSerializer):
    class Meta:
        model = Trader
        read_only_fields = ('id', 'created', 'modified', 'deleted_at')
        exclude = ['password']

    def create(self, validated_data):
        validated_data['role'] = UserRole.TRADER
        return super().create(validated_data)

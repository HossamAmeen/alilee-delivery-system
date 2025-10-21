from rest_framework import serializers

from users.models import Trader


class TraderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trader
        fields = '__all__'
        read_only_fields = ('id', 'created', 'modified', 'deleted_at')

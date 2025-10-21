from rest_framework.serializers import ModelSerializer

from transactions.models import TraderTransaction


class TraderTransactionSerializer(ModelSerializer):
    class Meta:
        model = TraderTransaction
        fields = '__all__'
        read_only_fields = ('id', 'created', 'modified', 'deleted_at')

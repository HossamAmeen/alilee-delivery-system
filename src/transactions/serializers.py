from django.shortcuts import get_object_or_404
from django.db.transaction import atomic
from rest_framework.serializers import ModelSerializer

from transactions.models import TraderTransaction, TransactionType
from users.models import Trader


class TraderTransactionSerializer(ModelSerializer):
    class Meta:
        model = TraderTransaction
        fields = ['id', 'user_account', 'amount', 'transaction_type', 'created', 'modified']
        read_only_fields = ('id', 'created', 'modified')

    @atomic
    def create(self, validated_data):
        trader = get_object_or_404(Trader, pk=validated_data['user_account'])
        if validated_data['transaction_type'] == TransactionType.WITHDRAW and validated_data['amount'] > trader.balance:
            from rest_framework import serializers
            raise serializers.ValidationError("Trader's balance is not enough.")

        trader_transaction = super().create(validated_data)
        if validated_data['transaction_type'] == TransactionType.WITHDRAW:
            trader.balance -= validated_data['amount']
        elif validated_data['transaction_type'] == TransactionType.DEPOSIT:
            trader.balance += validated_data['amount']

        trader.save()
        return trader_transaction

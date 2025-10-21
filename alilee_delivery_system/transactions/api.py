from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from transactions.models import TraderTransaction, TransactionType
from transactions.serializers import TraderTransactionSerializer
from users.models import Trader


class TraderTransactionViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, )
    queryset = TraderTransaction.objects.all()
    serializer_class = TraderTransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['transaction_type']
    ordering = ['-created']

    def create(self, request, *args, **kwargs):
        trader_transaction_serializer = self.serializer_class(data=request.data)
        trader_transaction_serializer.is_valid(raise_exception=True)

        trader = get_object_or_404(Trader, pk=request.data['user_account'])
        if(request.data['type'] == TransactionType.WITHDRAW and
            request.data['amount'] > trader.balance):
            trader_transaction_serializer.save()
            return Response({"message": "Trader\'s balance is not enough."},
                            status=status.HTTP_400_BAD_REQUEST)

        trader_transaction_serializer.save()
        return Response(trader_transaction_serializer.data, status=status.HTTP_201_CREATED)

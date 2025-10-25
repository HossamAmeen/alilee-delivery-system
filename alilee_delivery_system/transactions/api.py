from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from transactions.models import TraderTransaction
from transactions.serializers import TraderTransactionSerializer
from utilities.api import BaseViewSet


class TraderTransactionViewSet(BaseViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = TraderTransaction.objects.all()
    serializer_class = TraderTransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["transaction_type"]
    ordering = ["-created"]

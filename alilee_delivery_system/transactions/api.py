from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from transactions.models import TraderTransaction
from transactions.serializers import TraderTransactionSerializer


class TraderTransactionViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = TraderTransaction.objects.all()
    serializer_class = TraderTransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["transaction_type"]
    ordering = ["-created"]

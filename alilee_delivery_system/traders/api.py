from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny

from .models import Trader
from .serializers import TraderSerializer


#TODO: test and authenticate
class TraderViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Trader.objects.all()
    serializer_class = TraderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['email', 'full_name', 'phone_number', 'role', 'balance', 'status']
    search_fields = ['email', 'full_name', 'phone_number']
    ordering_fields = ['email', 'full_name', 'phone_number', 'role', 'balance', 'status']
    ordering = ['-created']

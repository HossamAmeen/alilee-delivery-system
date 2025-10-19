from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny

from .models import Manager
from .serializers import ManagerSerializer


class ManagerViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Manager.objects.all()
    serializer_class = ManagerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['email', 'full_name', 'phone_number', 'role']
    search_fields = ['email', 'full_name', 'phone_number']
    ordering_fields = ['email', 'full_name', 'phone_number', 'role']
    ordering = ['-created']
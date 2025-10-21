from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from users.models import UserAccount, Trader
from users.serializers.traders_serializers import TraderSerializer
from users.serializers.user_account_serializers import UserAccountSerializer, UserSerializer


#TODO: get and update account
class UserAccountViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['email', 'full_name', 'phone_number', 'role']
    search_fields = ['email', 'full_name', 'phone_number']
    ordering_fields = ['email', 'full_name', 'phone_number', 'role']
    ordering = ['-created']

    def create(self, request, *args, **kwargs):
        request.data['is_superuser'] = True
        user_serializer = UserSerializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        request.data['user'] = user_serializer.data['id']
        user_account_serializer = self.serializer_class(data=request.data)
        user_account_serializer.is_valid(raise_exception=True)
        user_account_serializer.save()
        return Response(user_account_serializer.data,
                        status=status.HTTP_201_CREATED)

class TraderViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Trader.objects.all()
    serializer_class = TraderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['email', 'full_name', 'phone_number', 'role', 'balance', 'status']
    search_fields = ['email', 'full_name', 'phone_number']
    ordering_fields = ['email', 'full_name', 'phone_number', 'role', 'balance', 'status']
    ordering = ['-created']

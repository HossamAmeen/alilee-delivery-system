from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from users.models import Trader, UserAccount
from users.serializers.traders_serializers import TraderSerializer
from users.serializers.user_account_serializers import UserAccountSerializer


class UserAccountViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["email", "full_name", "phone_number", "role"]
    search_fields = ["email", "full_name", "phone_number"]
    ordering_fields = ["email", "full_name", "phone_number", "role"]
    ordering = ["-id"]

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Return the current authenticated user"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"], permission_classes=[IsAuthenticated])
    def update_me(self, request):
        """Update the current authenticated user"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TraderViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Trader.objects.all()
    serializer_class = TraderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "email",
        "full_name",
        "phone_number",
        "role",
        "balance",
        "status",
    ]
    search_fields = ["email", "full_name", "phone_number"]
    ordering_fields = [
        "email",
        "full_name",
        "phone_number",
        "role",
        "balance",
        "status",
    ]
    ordering = ["-created"]

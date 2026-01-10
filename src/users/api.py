from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import UserAccount
from users.serializers.user_account_serializers import (
    FirebaseDeviceSerializer,
    UserAccountSerializer,
)
from utilities.api import BaseViewSet

from .models import FirebaseDevice


class UserAccountViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["email", "full_name", "phone_number", "role"]
    search_fields = ["email", "full_name", "phone_number"]
    ordering_fields = ["email", "full_name", "phone_number", "role"]
    ordering = ["-id"]

    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        request.data.pop("role", None)
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class FirebaseDeviceRegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=FirebaseDeviceSerializer)
    def post(self, request):
        serializer = FirebaseDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        user = request.user

        device, created = FirebaseDevice.objects.get_or_create(
            token=token,
            defaults={"user": user},
        )

        if not created and device.user != user:
            device.user = user
            device.save(update_fields=["user", "last_seen"])

        return Response(
            {
                "created": created,
                "token": device.token,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @swagger_auto_schema(request_body=FirebaseDeviceSerializer)
    def delete(self, request):
        serializer = FirebaseDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        FirebaseDevice.objects.filter(user=request.user, token=token).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

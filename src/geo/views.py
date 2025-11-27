from rest_framework.permissions import IsAuthenticated

from utilities.api import BaseViewSet

from .models import City, DeliveryZone
from .serializers import CitySerializer, DeliveryZoneSerializer


class CityViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = City.objects.all()
    serializer_class = CitySerializer


class DeliveryZoneViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    queryset = DeliveryZone.objects.all()
    serializer_class = DeliveryZoneSerializer
    filterset_fields = ["city"]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["-id"]

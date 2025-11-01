from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from trader_pricing.models import TraderDeliveryZone
from trader_pricing.serializers import TraderDeliveryZoneSerializer
from utilities.api import BaseViewSet


class TraderDeliveryZoneViewSet(BaseViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = TraderDeliveryZone.objects.all()
    serializer_class = TraderDeliveryZoneSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["trader", "delivery_zone"]
    ordering = ["-id"]

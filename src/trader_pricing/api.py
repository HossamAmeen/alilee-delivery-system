from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from trader_pricing.models import TraderDeliveryZone
from trader_pricing.serializers import TraderDeliveryZoneSerializer
from utilities.api import BaseViewSet
from trader_pricing.filters import TraderDeliveryZoneFilter
from trader_pricing.serializers import ListTraderDeliveryZoneSerializer


class TraderDeliveryZoneViewSet(BaseViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = TraderDeliveryZone.objects.order_by("-id").select_related("trader", "delivery_zone")
    serializer_class = TraderDeliveryZoneSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = TraderDeliveryZoneFilter
    ordering = ["-id"]

    def get_serializer_class(self):
        if self.action == "list":
            return ListTraderDeliveryZoneSerializer
        return super().get_serializer_class()
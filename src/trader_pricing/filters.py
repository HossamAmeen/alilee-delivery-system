import django_filters

from trader_pricing.models import TraderDeliveryZone


class TraderDeliveryZoneFilter(django_filters.FilterSet):
    class Meta:
        model = TraderDeliveryZone
        fields = {
            "trader": ["exact"],
            "delivery_zone": ["exact"],
        }

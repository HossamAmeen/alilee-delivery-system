import pytest

from geo.models import DeliveryZone
from trader_pricing.models import TraderDeliveryZone


@pytest.fixture
def delivery_zone(city):
    return DeliveryZone.objects.create(name="Test Zone", cost=10.00, city=city)


@pytest.fixture
def delivery_zone_2(city):
    return DeliveryZone.objects.create(name="Zone 2", cost=15.00, city=city)


@pytest.fixture
def trader_delivery_zone(trader, delivery_zone):
    return TraderDeliveryZone.objects.create(
        trader=trader,
        delivery_zone=delivery_zone,
        price=10.50,
    )


@pytest.fixture
def trader_delivery_zone_2(trader, delivery_zone_2):
    return TraderDeliveryZone.objects.create(
        trader=trader,
        delivery_zone=delivery_zone_2,
        price=15.00,
    )


@pytest.fixture
def delivery_zone_with_trader_2(trader_2, delivery_zone_2):
    return TraderDeliveryZone.objects.create(
        trader=trader_2,
        delivery_zone=delivery_zone_2,
        price=20.00,
    )

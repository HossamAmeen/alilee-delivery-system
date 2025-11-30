from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from geo.models import DeliveryZone
from orders.models import Customer, Order
from users.models import Driver, Trader, UserRole


@pytest.mark.django_db
def test_driver_retrieve_includes_delivery_totals(api_client, admin_user):
    # create users
    driver = Driver.objects.create_user(
        email="drv@example.com",
        password="test12345",
        full_name="Drv",
        role=UserRole.DRIVER,
    )

    trader = Trader.objects.create_user(
        email="tr@example.com",
        password="test12345",
        full_name="Tr",
        role=UserRole.TRADER,
    )

    dz = DeliveryZone.objects.create(
        name="Z1", cost=Decimal("5.00"), polygon="POINT(0 0)"
    )
    cust = Customer.objects.create(
        name="C1", address="A", phone="000", location="http://x"
    )

    # Delivered orders
    Order.objects.create(
        reference_code="O1",
        product_cost=Decimal("10.00"),
        delivery_cost=Decimal("12.50"),
        extra_delivery_cost=Decimal("3.50"),
        status="delivered",
        trader=trader,
        driver=driver,
        customer=cust,
        delivery_zone=dz,
    )

    Order.objects.create(
        reference_code="O2",
        product_cost=Decimal("20.00"),
        delivery_cost=Decimal("7.50"),
        extra_delivery_cost=Decimal("1.50"),
        status="delivered",
        trader=trader,
        driver=driver,
        customer=cust,
        delivery_zone=dz,
    )

    api_client.force_authenticate(user=admin_user)
    url = reverse("drivers-detail", kwargs={"pk": driver.id})
    resp = api_client.get(url)

    assert resp.status_code == status.HTTP_200_OK

    # totals from delivered orders
    assert Decimal(str(resp.data.get("total_delivery_cost"))) == Decimal("20.00")
    assert Decimal(str(resp.data.get("total_extra_delivery_cost"))) == Decimal("5.00")
    assert Decimal(str(resp.data.get("total_delivery_earnings"))) == Decimal("25.00")

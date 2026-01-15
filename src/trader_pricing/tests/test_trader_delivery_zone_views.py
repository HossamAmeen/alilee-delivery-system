from decimal import Decimal

from django.urls import reverse
from rest_framework import status


class TestTraderDeliveryZoneViewSet:
    def setup_method(self):
        self.list_url = reverse("trader-delivery-zones-list")
        self.detail_url = lambda id: reverse("trader-delivery-zones-detail", args=[id])

    def test_list_trader_delivery_zones_success(
        self, admin_client, trader_delivery_zone, trader_delivery_zone_2
    ):
        """Test listing trader delivery zones as an authenticated user."""
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert response.data["results"][1]["id"] == trader_delivery_zone.id
        assert response.data["results"][0]["id"] == trader_delivery_zone_2.id

    def test_list_trader_delivery_zones_unauthenticated_failed(self, api_client):
        """Test that unauthenticated users cannot access the list."""
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_trader_delivery_zone_success(
        self, admin_client, trader_delivery_zone
    ):
        """Test retrieving a single trader delivery zone."""
        response = admin_client.get(self.detail_url(trader_delivery_zone.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == trader_delivery_zone.id
        assert response.data["trader"]["id"] == trader_delivery_zone.trader.id
        assert (
            response.data["delivery_zone"]["id"]
            == trader_delivery_zone.delivery_zone.id
        )
        assert Decimal(response.data["price"]) == trader_delivery_zone.price

    def test_list_filter_by_trader(
        self,
        admin_client,
        trader,
        trader_delivery_zone,
        delivery_zone,
        delivery_zone_with_trader_2,
    ):
        """Test filtering trader delivery zones by trader."""

        response = admin_client.get(self.list_url + f"?trader={trader.id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == trader_delivery_zone.id

    def test_search_by_delivery_zone_name(
        self,
        admin_client,
        delivery_zone_with_trader_2,
        trader_delivery_zone_2,
        trader_delivery_zone,
    ):
        """Test searching trader delivery zones by delivery zone name."""
        search_term = trader_delivery_zone.delivery_zone.name.split()[
            0
        ]  # Get the first word of the zone name
        response = admin_client.get(self.list_url + f"?search={search_term}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert (
            response.data["results"][0]["delivery_zone"]["id"]
            == trader_delivery_zone.delivery_zone.id
        )

    def test_create_trader_delivery_zone(self, admin_client, trader, delivery_zone):
        """Test creating a new trader delivery zone."""
        data = {
            "trader": str(trader.id),
            "delivery_zone": str(delivery_zone.id),
            "price": "15.99",
        }
        response = admin_client.post(self.list_url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["price"] == data["price"]

    def test_update_trader_delivery_zone(self, admin_client, trader_delivery_zone):
        """Test updating a trader delivery zone."""
        data = {
            "price": "20.00",
            "trader": str(trader_delivery_zone.trader.id),
            "delivery_zone": str(trader_delivery_zone.delivery_zone.id),
        }
        response = admin_client.put(
            self.detail_url(trader_delivery_zone.id), data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["price"] == "20.00"

    def test_partial_update_trader_delivery_zone(
        self, admin_client, trader_delivery_zone
    ):
        """Test partially updating a trader delivery zone."""
        data = {"price": "25.50"}
        response = admin_client.patch(
            self.detail_url(trader_delivery_zone.id), data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["price"] == "25.50"

    def test_delete_trader_delivery_zone(self, admin_client, trader_delivery_zone):
        """Test deleting a trader delivery zone."""
        response = admin_client.delete(self.detail_url(trader_delivery_zone.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

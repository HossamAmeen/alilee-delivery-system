from rest_framework import status
from rest_framework.reverse import reverse

from orders.models import ProductPaymentStatus


class TestRetrieveOrder:
    def test_retrieve_order_with_product_payment_status_cod_success(
        self, admin_client, driver_client, assigned_order
    ):
        url = reverse("orders-detail", kwargs={"pk": assigned_order.id})

        response = driver_client.get(url, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        assert response.data["product_payment_status"] == "cod"
        assert response.data["total_cost"] == assigned_order.product_cost

    def test_retrieve_order_with_product_payment_status_paid_success(
        self, driver_client, assigned_order
    ):
        assigned_order.product_payment_status = ProductPaymentStatus.PAID
        assigned_order.save()

        url = reverse("orders-detail", kwargs={"pk": assigned_order.id})

        response = driver_client.get(url, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        assert response.data["product_payment_status"] == ProductPaymentStatus.PAID
        assert response.data["total_cost"] == 0

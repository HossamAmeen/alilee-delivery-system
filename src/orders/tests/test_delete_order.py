from rest_framework import status
from rest_framework.reverse import reverse
from transactions.models import TransactionType, UserAccountTransaction


class TestDeleteOrder:
    def test_delete_order_with_status_success(self, admin_client, assigned_order):
        url = reverse("orders-detail", kwargs={"pk": assigned_order.id})

        response = admin_client.delete(url, format="json")
        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), f"Expected 204 No Content, got {response.status_code}. Response: {response.data}"

    def test_delete_order_with_status_not_cancelled_fail(
        self, admin_client, assigned_order
    ):
        UserAccountTransaction.objects.create(
            order=assigned_order,
            user_account=assigned_order.trader,
            amount=assigned_order.product_cost,
            transaction_type=TransactionType.WITHDRAW,
        )
        url = reverse("orders-detail", kwargs={"pk": assigned_order.id})

        response = admin_client.delete(url, format="json")

        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), f"Expected 400 Bad Request, got {response.status_code}. Response: {response.data}"
        assert (
            response.data["message"] == "لا يمكن حذف الطلب لأنه يحتوي على عمليات مالية"
        )

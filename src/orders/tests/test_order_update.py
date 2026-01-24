"""
Unit tests for order update endpoint using pytest.

This module tests the order update functionality through the REST API,
ensuring proper validation, authentication, and business rules are enforced.
"""

from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from orders.models import OrderStatus, ProductPaymentStatus
from transactions.models import TransactionType, UserAccountTransaction


class TestUpdateOrder:
    def test_unauthorized_update(self, api_client, created_order):
        url = reverse("orders-detail", kwargs={"pk": created_order.id})

        update_payload = {"product_cost": "150.00"}

        response = api_client.patch(url, data=update_payload, format="json")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ], f"Expected 401 or 403, got {response.status_code}. Response: {response.data}"

    def test_update_order_non_existing_fail(self, admin_client):
        url = reverse("orders-detail", kwargs={"pk": -1})

        update_payload = {"note": "REF99999"}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        ), f"Expected 404 Not Found, got {response.status_code}"

    def test_update_order_with_customer_changes_success(
        self, admin_client, created_order
    ):
        url = reverse("orders-detail", kwargs={"pk": created_order.id})

        update_payload = {
            "customer": {
                "id": created_order.customer.id,
                "phone": "1234567890",
                "address": "updated",
            }
        }

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

    def test_update_order_with_product_payment_status_cod_success(
        self, admin_client, driver_client, created_order, driver
    ):
        url = reverse("orders-detail", kwargs={"pk": created_order.id})

        update_payload = {"status": OrderStatus.IN_PROGRESS}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        update_payload = {"driver": driver.id}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED, "Status should be updated"
        assert created_order.driver == driver, "Driver should be updated"

        update_payload = {"status": OrderStatus.DELIVERED}

        response = driver_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.DELIVERED, "Status should be updated"

        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=driver.id
            ).count()
            == 2
        ), "Transaction should be created"
        driver.refresh_from_db()

        assert driver.balance == created_order.product_cost - (
            created_order.delivery_cost + created_order.extra_delivery_cost
        ), "Driver balance should be updated"

        trader = created_order.trader
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=trader.id
            ).count()
            == 2
        ), "Transaction should be created"
        trader.refresh_from_db()
        assert (
            trader.balance
            == -1 * created_order.product_cost + created_order.trader_cost
        ), "Trader balance should be updated"

    def test_update_order_postponed_with_order_payment_status_cod_success(
        self, admin_client, driver_client, created_order, driver
    ):
        url = reverse("orders-detail", kwargs={"pk": created_order.id})

        update_payload = {"status": OrderStatus.IN_PROGRESS}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        update_payload = {"driver": driver.id}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED, "Status should be updated"
        assert created_order.driver == driver, "Driver should be updated"

        # update order status to POSTPONED
        update_payload = {"status": OrderStatus.POSTPONED}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.POSTPONED, "Status should be updated"
        assert created_order.postpone_count == 1, "Postpone count should be updated"

        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=driver.id
            ).count()
            == 0
        ), "no transaction for driver"
        driver.refresh_from_db()

        assert driver.balance == 0, "Driver balance should not be updated"

        trader = created_order.trader
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=trader.id
            ).count()
            == 0
        ), "no transaction for trader"
        trader.refresh_from_db()
        assert trader.balance == 0, "Trader balance should not be updated"

    def test_update_order_postponed_with_order_payment_status_paid_success(
        self, admin_client, driver_client, created_order, driver
    ):
        created_order.product_payment_status = ProductPaymentStatus.PAID
        created_order.save()

        url = reverse("orders-detail", kwargs={"pk": created_order.id})

        update_payload = {"status": OrderStatus.IN_PROGRESS}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        update_payload = {"driver": driver.id}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED, "Status should be updated"
        assert created_order.driver == driver, "Driver should be updated"

        # update order status to POSTPONED
        update_payload = {"status": OrderStatus.POSTPONED}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.POSTPONED, "Status should be updated"
        assert created_order.postpone_count == 1, "Postpone count should be updated"

        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=driver.id
            ).count()
            == 0
        ), "no transaction for driver"
        driver.refresh_from_db()

        assert driver.balance == 0, "Driver balance should not be updated"

        trader = created_order.trader
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id,
                user_account_id=trader.id,
                amount=created_order.trader_cost,
            ).count()
            == 1
        ), "no transaction for trader"
        trader.refresh_from_db()
        assert (
            trader.balance == created_order.trader_cost
        ), "Trader balance should not be updated"

    def test_update_order_with_product_payment_status_paid_success(
        self, admin_client, driver_client, created_order, driver
    ):
        url = reverse("orders-detail", kwargs={"pk": created_order.id})
        created_order.product_payment_status = ProductPaymentStatus.PAID
        created_order.save()

        update_payload = {"status": OrderStatus.IN_PROGRESS}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        update_payload = {"driver": driver.id}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED, "Status should be updated"
        assert created_order.driver == driver, "Driver should be updated"

        update_payload = {"status": OrderStatus.DELIVERED}

        response = driver_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.DELIVERED, "Status should be updated"

        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=driver.id
            ).count()
            == 1
        ), "Transaction should be created"
        driver.refresh_from_db()

        assert driver.balance == -1 * (
            created_order.delivery_cost + created_order.extra_delivery_cost
        ), "Driver balance should be updated"

        trader = created_order.trader
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=trader.id
            ).count()
            == 1
        ), "Transaction should be created"
        trader.refresh_from_db()
        assert (
            trader.balance == created_order.trader_cost
        ), "Trader balance should be updated"

    def test_update_order_with_product_payment_status_paid_and_cancelled_success(
        self, admin_client, driver_client, created_order, driver
    ):
        old_driver_balance = driver.balance
        url = reverse("orders-detail", kwargs={"pk": created_order.id})
        created_order.product_payment_status = ProductPaymentStatus.PAID
        created_order.save()

        update_payload = {"status": OrderStatus.IN_PROGRESS}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        update_payload = {"driver": driver.id}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED, "Status should be updated"
        assert created_order.driver == driver, "Driver should be updated"

        update_payload = {"status": OrderStatus.CANCELLED}

        response = driver_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.CANCELLED, "Status should be updated"

        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=driver.id
            ).count()
            == 0
        ), "Transaction should not be created"
        driver.refresh_from_db()

        assert driver.balance == old_driver_balance, "Driver balance should be updated"

        trader = created_order.trader
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=trader.id
            ).count()
            == 1
        ), "Transaction should be created"
        trader.refresh_from_db()

        assert (
            trader.balance == created_order.trader_cost
        ), "Trader balance should be updated"

    def test_update_order_with_product_payment_status_COD_and_cancelled_success(
        self, admin_client, driver_client, created_order, driver
    ):
        old_driver_balance = driver.balance
        old_trader_balance = created_order.trader.balance
        url = reverse("orders-detail", kwargs={"pk": created_order.id})
        created_order.product_payment_status = ProductPaymentStatus.COD
        created_order.save()

        update_payload = {"status": OrderStatus.IN_PROGRESS}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        update_payload = {"driver": driver.id}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED, "Status should be updated"
        assert created_order.driver == driver, "Driver should be updated"

        update_payload = {"status": OrderStatus.CANCELLED}

        response = driver_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.CANCELLED, "Status should be updated"

        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=driver.id
            ).count()
            == 0
        ), "Transaction should not be created"
        driver.refresh_from_db()

        assert driver.balance == old_driver_balance, "Driver balance should be updated"

        trader = created_order.trader
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=trader.id
            ).count()
            == 0
        ), "Transaction should not be created"
        trader.refresh_from_db()
        assert trader.balance == old_trader_balance, "Trader balance should be updated"

    def test_delivered_order_after_delivered(
        self, admin_client, driver_client, created_order, driver
    ):
        url = reverse("orders-detail", kwargs={"pk": created_order.id})
        update_payload = {"status": OrderStatus.IN_PROGRESS}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        update_payload = {"driver": driver.id}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED, "Status should be updated"
        assert created_order.driver == driver, "Driver should be updated"

        update_payload = {"status": OrderStatus.DELIVERED}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.DELIVERED, "Status should be updated"

        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=driver.id
            ).count()
            == 2
        ), "Transaction should be created"

        # update order status to delivered again
        response = admin_client.patch(url, data=update_payload, format="json")
        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), f"Expected 400 Bad Request, got {response.status_code}. Response: {response.data}"
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=driver.id
            ).count()
            == 2
        ), "Transaction should be created"

    def test_update_order_rolled_back_success(
        self, admin_client, driver_client, created_order, assigned_order, driver
    ):
        # generate transaction to avoid id conflict
        UserAccountTransaction.objects.create(
            order_id=assigned_order.id,
            user_account_id=driver.id,
            amount=assigned_order.product_cost
            - (assigned_order.delivery_cost + assigned_order.extra_delivery_cost),
            is_rolled_back=False,
            transaction_type=TransactionType.WITHDRAW,
        )
        UserAccountTransaction.objects.create(
            order_id=assigned_order.id,
            user_account_id=assigned_order.trader.id,
            amount=assigned_order.product_cost
            - (assigned_order.delivery_cost + assigned_order.extra_delivery_cost),
            is_rolled_back=False,
            transaction_type=TransactionType.DEPOSIT,
        )

        driver.balance = Decimal(0)
        driver.save()
        assigned_order.trader.balance = Decimal(0)
        assigned_order.trader.save()

        url = reverse("orders-detail", kwargs={"pk": created_order.id})
        created_order.product_payment_status = ProductPaymentStatus.COD
        created_order.save()

        update_payload = {"status": OrderStatus.IN_PROGRESS}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        update_payload = {"driver": driver.id}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.ASSIGNED, "Status should be updated"
        assert created_order.driver == driver, "Driver should be updated"

        old_driver_balance = driver.balance
        assert old_driver_balance == 0
        old_trader_balance = created_order.trader.balance
        assert old_trader_balance == 0
        update_payload = {"status": OrderStatus.DELIVERED}

        response = driver_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.DELIVERED, "Status should be updated"

        assert UserAccountTransaction.objects.filter(
            order_id=created_order.id,
            user_account_id=driver.id,
            transaction_type=TransactionType.WITHDRAW,
            amount=created_order.product_cost,
        ).exists(), "Transaction with withdraw type with product cost should be created for dirver."

        assert UserAccountTransaction.objects.filter(
            order_id=created_order.id,
            user_account_id=driver.id,
            transaction_type=TransactionType.DEPOSIT,
            amount=created_order.delivery_cost + created_order.extra_delivery_cost,
        ).exists(), "Transaction with deposit type with delivery cost should be created for dirver."
        driver.refresh_from_db()

        assert driver.balance == created_order.product_cost - (
            created_order.delivery_cost + created_order.extra_delivery_cost
        ), "Driver balance should be updated"

        trader = created_order.trader
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id, user_account_id=trader.id
            ).count()
            == 2
        ), "Transaction should be created"
        trader.refresh_from_db()
        assert (
            trader.balance
            == -1 * created_order.product_cost + created_order.trader_cost
        ), "Trader balance should be updated"

        # update order status to created (rolled back)
        update_payload = {"status": OrderStatus.CREATED}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.status == OrderStatus.CREATED, "Status should be updated"
        assert created_order.driver is None, "Driver should be deleted"

        trader.refresh_from_db()
        assert (
            trader.balance == old_trader_balance
        ), "Trader balance should not be updated"

        driver.refresh_from_db()
        assert (
            driver.balance == old_driver_balance
        ), "Driver balance should not be updated"
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id,
                user_account_id=driver.id,
                is_rolled_back=True,
            ).count()
            == 4
        ), "Transaction should be rolled back for driver"
        assert (
            UserAccountTransaction.objects.filter(
                order_id=created_order.id,
                user_account_id=trader.id,
                is_rolled_back=True,
            ).count()
            == 4
        ), "Transaction should be rolled back for trader"

    def test_update_order_to_assigned_without_driver(self, admin_client, created_order):
        url = reverse("orders-detail", kwargs={"pk": created_order.id})
        update_payload = {"status": OrderStatus.ASSIGNED}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), f"Expected 400 Bad Request, got {response.status_code}. Response: {response.data}"
        assert (
            response.data["message"] == "يجب تعين سائق للطلب"
        ), "Driver should be updated"

    def test_update_product_price_with_delivered_order_failed(
        self, admin_client, created_order
    ):
        created_order.status = OrderStatus.DELIVERED
        extra_delivery_cost = created_order.extra_delivery_cost
        created_order.save()

        url = reverse("orders-detail", kwargs={"pk": created_order.id})
        update_payload = {"extra_delivery_cost": 100}

        response = admin_client.patch(url, data=update_payload, format="json")

        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), f"Expected 400 Bad Request, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert (
            created_order.extra_delivery_cost == extra_delivery_cost
        ), "Extra delivery cost should not be updated"

    def test_update_order_image_success(self, admin_client, created_order):
        url = reverse("orders-detail", kwargs={"pk": created_order.id})

        # Create a small dummy image
        image_content = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b"
        image = SimpleUploadedFile(
            "test_image.gif", image_content, content_type="image/gif"
        )

        update_payload = {"image": image}

        # Note: When sending files, we should not use format="json"
        response = admin_client.patch(url, data=update_payload, format="multipart")

        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Expected 200 OK, got {response.status_code}. Response: {response.data}"

        created_order.refresh_from_db()
        assert created_order.image is not None, "Image should be uploaded"
        assert created_order.image.name.endswith(
            ".gif"
        ), "Image file name should end with .gif"

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from orders.models import Customer, Order, OrderStatus


@pytest.mark.django_db
class TestOrderExportCSV:
    def setup_method(self):
        self.url = reverse("orders-export-csv")

    def test_export_csv_success(self, admin_client, trader, assigned_order):
        response = admin_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        assert (
            'attachment; filename="orders_export.csv"'
            in response["Content-Disposition"]
        )

        content = response.content.decode("utf-8")
        lines = content.strip().split("\n")
        assert len(lines) >= 2  # Header + at least one order
        assert (
            "تاريخ الاضافة,رقم التتبع,رمز المرجع,اسم التاجر,العنوان,الحالة,حالة الدفع,رسوم الشحن,فلوس المكتب,فلوس التاجر,فرق الفلوس"
            in lines[0]
        )
        assert assigned_order.tracking_number in lines[1]

    def test_export_csv_filter_by_trader(
        self, admin_client, trader, trader_2, assigned_order, delivery_zone
    ):
        # Create another order for trader_2
        customer2 = Customer.objects.create(
            name="Jane Doe", address="456 Side St", phone="+209876543210"
        )
        order2 = Order.objects.create(
            tracking_number="999999999999",
            reference_code="REF999",
            product_cost=Decimal("200.00"),
            delivery_zone=delivery_zone,
            trader=trader_2,
            status=OrderStatus.CREATED,
            customer=customer2,
        )

        # Filter by trader 1
        response = admin_client.get(self.url, {"trader": trader.id})
        content = response.content.decode("utf-8")
        assert assigned_order.tracking_number in content
        assert order2.tracking_number not in content

        # Filter by trader 2
        response = admin_client.get(self.url, {"trader": trader_2.id})
        content = response.content.decode("utf-8")
        assert assigned_order.tracking_number not in content
        assert order2.tracking_number in content

    def test_export_csv_filter_by_tracking_numbers(
        self, admin_client, assigned_order, delivery_zone, trader
    ):
        customer2 = Customer.objects.create(
            name="Jane Doe", address="456 Side St", phone="+209876543210"
        )
        order2 = Order.objects.create(
            tracking_number="888888888888",
            reference_code="REF888",
            product_cost=Decimal("200.00"),
            delivery_zone=delivery_zone,
            trader=trader,
            status=OrderStatus.CREATED,
            customer=customer2,
        )

        response = admin_client.get(
            self.url, {"tracking_numbers": f"{assigned_order.tracking_number}"}
        )
        content = response.content.decode("utf-8")
        assert assigned_order.tracking_number in content
        assert order2.tracking_number not in content

    def test_export_csv_filter_by_reference_codes(
        self, admin_client, assigned_order, delivery_zone, trader
    ):
        customer2 = Customer.objects.create(
            name="Jane Doe", address="456 Side St", phone="+209876543210"
        )
        order2 = Order.objects.create(
            tracking_number="777777777777",
            reference_code="REF777",
            product_cost=Decimal("200.00"),
            delivery_zone=delivery_zone,
            trader=trader,
            status=OrderStatus.CREATED,
            customer=customer2,
        )

        response = admin_client.get(
            self.url, {"reference_codes": f"{assigned_order.reference_code}"}
        )
        content = response.content.decode("utf-8")
        assert assigned_order.reference_code in content
        assert order2.reference_code not in content

    def test_export_csv_filter_by_date_range_success(
        self, admin_client, assigned_order
    ):
        date_str = assigned_order.created.strftime("%Y-%m-%d")
        response = admin_client.get(
            self.url, {"date_from": date_str, "date_to": date_str}
        )

        assert response.status_code == status.HTTP_200_OK
        content = response.content.decode("utf-8")
        assert assigned_order.tracking_number in content

    def test_export_csv_date_range_exceeds_7_days(self, admin_client):
        response = admin_client.get(
            self.url, {"date_from": "2023-01-01", "date_to": "2023-01-10"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["message"] == "Date range cannot exceed 7 days."

    def test_export_csv_invalid_date_format(self, admin_client):
        response = admin_client.get(
            self.url, {"date_from": "01-01-2023", "date_to": "10-01-2023"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["message"] == "Invalid date format. Use YYYY-MM-DD."

    def test_export_csv_count_limit_exceeded(self, admin_client):
        # Mock the count method to return > 5000
        with patch("django.db.models.query.QuerySet.count", return_value=5001):
            response = admin_client.get(self.url)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert (
                response.data["message"]
                == "Cannot export more than 5000 orders at once."
            )

import uuid
from decimal import Decimal

from django.core.validators import RegexValidator
from django.db import models

from utilities.models.abstract_base_model import AbstractBaseModel


class OrderStatus(models.TextChoices):
    CREATED = "created", "Created"
    ASSIGNED = "assigned_to_driver", "Assigned to Driver"
    IN_PROGRESS = "in_progress", "In Progress"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"
    POSTPONED = "postponed", "Postponed"


class PaymentMethod(models.TextChoices):
    PAID = "paid", "Paid"
    COD = "cod", "Cash on Delivery"
    REMAINING_FEES = "remaining_fees", "Remaining Shipping Fees"


class ProductPaymentStatus(models.TextChoices):
    PAID = "paid", "Paid"
    UNPAID = "unpaid", "Unpaid"
    REMAINING_FEES = "remaining_fees", "Remaining Shipping Fees"
    COD = "cod", "Cash on Delivery"


class Customer(AbstractBaseModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    location = models.URLField(null=True, blank=True)


class Order(AbstractBaseModel):
    tracking_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(r"^\d+$", "Tracking number must contain only digits.")
        ],
        editable=False,
    )
    reference_code = models.CharField(max_length=15, unique=True)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.CREATED,
    )

    # Cost
    product_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )  # total before shipping
    delivery_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    extra_delivery_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    product_payment_status = models.CharField(
        max_length=20,
        choices=ProductPaymentStatus.choices,
        default=ProductPaymentStatus.COD,
    )
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    trader_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    trader_merchant_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    note = models.TextField(null=True, blank=True)
    status_changed_at = models.DateTimeField(auto_now=True, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=10, null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=10, null=True)
    cancel_reason = models.TextField(null=True, blank=True)
    postpone_reason = models.TextField(null=True, blank=True)
    postpone_count = models.IntegerField(default=0)
    is_return = models.BooleanField(default=False, verbose_name="Is Return Order")
    image = models.ImageField(upload_to="orders/images", null=True, blank=True)

    # Relations
    driver = models.ForeignKey(
        "users.Driver",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    trader = models.ForeignKey(
        "users.Trader",
        null=True,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    customer = models.ForeignKey(
        "orders.Customer",
        null=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    delivery_zone = models.ForeignKey(
        "geo.DeliveryZone",
        null=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = str(uuid.uuid4().int)[:12]
        self.total_cost = 0  # TODO: calculate total cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.tracking_number}"

    # Arabic display mapping for status codes — accessible from the model
    STATUS_AR = {
        "created": "تم الإنشاء",
        "assigned_to_driver": "معين للسائق",
        "in_progress": "قيد التوصيل",
        "delivered": "تم التوصيل",
        "cancelled": "ملغى",
        "postponed": "مؤجل",
    }

    PRODUCT_PAYMENT_STATUS_AR = {
        "paid": "مدفوعه",
        "unpaid": "غير مدفوع",
        "remaining_fees": "رسوم الشحن",
        "cod": "دفع عند الاستلام",
    }

    STATUS_COLOR = {
        "created": "#2196F3",  # Blue for new orders
        "assigned_to_driver": "#FFC107",  # Amber for assigned orders
        "in_progress": "#3F51B5",  # Indigo for in-progress orders
        "delivered": "#4CAF50",  # Green for delivered orders
        "cancelled": "#F44336",  # Red for cancelled orders
        "postponed": "#9C27B0",  # Purple for postponed orders
    }

    @property
    def status_ar(self):
        """Return the Arabic label for the current order status."""
        return self.STATUS_AR.get(self.status, self.status)

    @property
    def product_payment_status_ar(self):
        """Return the Arabic label for the current order product payment status."""
        return self.PRODUCT_PAYMENT_STATUS_AR.get(
            self.product_payment_status, self.product_payment_status
        )

    @property
    def total_cost_for_driver(self):
        if self.product_payment_status == ProductPaymentStatus.PAID:
            return 0
        else:
            return self.product_cost

    @property
    def status_color(self):
        return self.STATUS_COLOR.get(self.status, self.status)

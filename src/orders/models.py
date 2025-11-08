import uuid
from django.db import models
from django.core.validators import RegexValidator

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


class Customer(AbstractBaseModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    location = models.URLField(null=True, blank=True)


class Order(AbstractBaseModel):
    tracking_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r"^\d+$", "Tracking number must contain only digits.")],
        editable=False,
    )
    code = models.CharField(max_length=4)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.CREATED,
    )

    # Cost
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)  # total before shipping
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2)
    extra_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD,
    )
    note = models.TextField(null=True, blank=True)

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
        on_delete=models.SET_NULL,
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
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.tracking_number}"

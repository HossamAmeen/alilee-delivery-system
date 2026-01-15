from django.db import models

from geo.models import DeliveryZone
from users.models import Trader
from utilities.models.abstract_base_model import AbstractBaseModel


class TraderDeliveryZone(AbstractBaseModel):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.SET_NULL,
        null=True,
        related_name="trader_delivery_zones",
    )
    trader = models.ForeignKey(
        Trader,
        on_delete=models.SET_NULL,
        related_name="trader_delivery_zones_trader",
        null=True,
    )

    class Meta:
        unique_together = ("delivery_zone", "trader")
        constraints = [
            models.UniqueConstraint(
                fields=["delivery_zone", "trader"],
                name="unique_trader_delivery_zone",
                violation_error_message="هذا التاجر لديه بالفعل تسعيرة لهذه المنطقة",
            )
        ]

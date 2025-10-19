from django.db import models
from users.models import UserAccount


class TraderStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    SUSPENDED = 'suspended', 'Suspended'


class Trader(UserAccount):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=10,
        choices=TraderStatus.choices,
        default=TraderStatus.ACTIVE
    )

    class Meta:
        verbose_name = 'Trader'
        verbose_name_plural = 'Traders'
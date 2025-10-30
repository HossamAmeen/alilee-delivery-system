from django.db import models

from users.models import UserAccount
from utilities.models.abstract_base_model import AbstractBaseModel


class UserAccountTransaction(AbstractBaseModel):
    class Meta:
        abstract = True

    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    user_account = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        related_name="user_account",
        null=True,
    )


class TransactionType(models.TextChoices):
    WITHDRAW = "withdraw", "withdraw"
    DEPOSIT = "deposit", "deposit"


class TraderTransaction(UserAccountTransaction):
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)

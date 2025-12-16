from django.db import models

from orders.models import Order
from users.models import UserAccount
from utilities.models.abstract_base_model import AbstractBaseModel


class TransactionType(models.TextChoices):
    WITHDRAW = "withdraw", "withdraw"
    DEPOSIT = "deposit", "deposit"


class UserAccountTransaction(AbstractBaseModel):
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    file = models.FileField(upload_to="transaction_files/", blank=True, null=True)
    notes = models.TextField(blank=True)
    is_rolled_back = models.BooleanField(default=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
    )
    user_account = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
    )


class Expense(AbstractBaseModel):
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

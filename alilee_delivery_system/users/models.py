from django.contrib.auth.models import User
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django_softdelete.models import SoftDeleteModel


class UserRole(models.TextChoices):
    OWNER = 'owner', 'owner'
    MANAGER = 'manager', 'manager'
    ADMIN = 'admin', 'admin'
    TRADER = 'trader', 'trader'

class UserAccount(SoftDeleteModel, TimeStampedModel):
    email = models.TextField('Email', unique=True)
    full_name = models.TextField('Full Name', null=True)
    phone_number = models.CharField(max_length=11)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.ADMIN
    )
    user = models.OneToOneField(User, on_delete=models.SET_NULL,
                                related_name="account_user", null=True)


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

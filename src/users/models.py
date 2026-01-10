from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models

from users.manager import UserAccountManager
from utilities.models.abstract_base_model import AbstractBaseModel


class UserRole(models.TextChoices):
    OWNER = "owner", "owner"
    MANAGER = "manager", "manager"
    ADMIN = "admin", "admin"
    TRADER = "trader", "trader"
    DRIVER = "driver", "driver"


class UserAccount(AbstractUser, AbstractBaseModel):
    username = first_name = last_name = date_joined = None

    email = models.EmailField("Email", unique=True)
    full_name = models.CharField("Full Name", max_length=255)
    phone_number = models.CharField(max_length=11, null=True)
    role = models.CharField(
        max_length=10, choices=UserRole.choices, default=UserRole.ADMIN
    )

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_user_account_role(self):
        if self.role == UserRole.DRIVER:
            return Driver
        elif self.role == UserRole.TRADER:
            return Trader
        return None

    def update_balance(self, amount):
        if self.role == UserRole.DRIVER:
            self.driver.balance += Decimal(amount)
            self.driver.save()
        if self.role == UserRole.TRADER:
            self.trader.balance += Decimal(amount)
            self.trader.save()


class TraderStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"


class Trader(UserAccount):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=10,
        choices=TraderStatus.choices,
        default=TraderStatus.ACTIVE,
    )

    def save(self, **kwargs):
        self.role = UserRole.TRADER
        return super().save(**kwargs)

    class Meta:
        verbose_name = "Trader"
        verbose_name_plural = "Traders"


class Driver(UserAccount):
    vehicle_number = models.CharField(max_length=20, null=True)
    license_number = models.CharField(max_length=20, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, **kwargs):
        self.role = UserRole.DRIVER
        return super().save(**kwargs)

    class Meta:
        verbose_name = "Driver"
        verbose_name_plural = "Drivers"


class FirebaseDevice(models.Model):
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name="firebase_devices",
    )

    token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )

    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "token"]),
        ]

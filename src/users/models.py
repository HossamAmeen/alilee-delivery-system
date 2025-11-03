from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from utilities.models.abstract_base_model import AbstractBaseModel


class UserRole(models.TextChoices):
    OWNER = "owner", "owner"
    MANAGER = "manager", "manager"
    ADMIN = "admin", "admin"
    TRADER = "trader", "trader"


class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class UserAccount(AbstractUser, PermissionsMixin, AbstractBaseModel):
    email = models.EmailField("Email", unique=True)
    full_name = models.CharField("Full Name", max_length=255)
    phone_number = models.CharField(max_length=11, null=True)
    role = models.CharField(
        max_length=10, choices=UserRole.choices, default=UserRole.ADMIN
    )
    username = None
    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


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

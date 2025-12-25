from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from utilities.exceptions import CustomValidationError
from utilities.models.abstract_base_model import AbstractBaseModel


class UserRole(models.TextChoices):
    OWNER = "owner", "owner"
    MANAGER = "manager", "manager"
    ADMIN = "admin", "admin"
    TRADER = "trader", "trader"
    DRIVER = "driver", "driver"


class UserAccountManager(UserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise CustomValidationError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, username=None, email=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


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
            self.driver.balance += amount
            self.driver.save()
        if self.role == UserRole.TRADER:
            self.trader.balance += amount
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



class Driver(UserAccount):
    vehicle_number = models.CharField(max_length=20, null=True)
    license_number = models.CharField(max_length=20, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, **kwargs):
        self.role = UserRole.DRIVER
        return super().save(**kwargs)


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

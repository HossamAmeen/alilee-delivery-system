from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models
from django_softdelete.models import SoftDeleteModel
from utils.abstract_base_model import AbstractBaseModel


class UserRole(models.TextChoices):
    OWNER = 'owner', 'owner'
    MANAGER = 'manager', 'manager'
    ADMIN = 'admin', 'admin'
    TRADER = 'trader', 'trader'


class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class UserAccount(AbstractUser, SoftDeleteModel, AbstractBaseModel):
    email = models.EmailField('Email', unique=True)
    full_name = models.CharField('Full Name', max_length=100)
    phone_number = models.CharField(max_length=11, null=True)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.ADMIN
    )
    created_by = models.ForeignKey('self', on_delete=models.CASCADE, related_name="created_%(class)ss", null=True, blank=True)
    updated_by = models.ForeignKey('self', on_delete=models.CASCADE, related_name="updated_%(class)ss", null=True, blank=True)

    objects = UserAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


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

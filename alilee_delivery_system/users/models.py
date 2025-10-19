from django.db import models
from django_extensions.db.models import TimeStampedModel
from django_softdelete.models import SoftDeleteModel


class UserRole(models.TextChoices):
    OWNER = 'owner', 'owner'
    MANAGER = 'manager', 'manager'
    ADMIN = 'admin', 'admin'


class UserAccount(SoftDeleteModel, TimeStampedModel):
    class Meta:
        abstract = True

    email = models.TextField('Email', unique=True)
    full_name = models.TextField('Full Name', null=True)
    phone_number = models.CharField(max_length=11)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.ADMIN
    )

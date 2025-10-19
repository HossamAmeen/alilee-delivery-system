from django.db import models
from users.models import UserAccount


class Manager(UserAccount):
    class Meta:
        verbose_name = 'Manager'
        verbose_name_plural = 'Managers'

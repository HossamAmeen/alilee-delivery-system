from django.db import models

from users.models import UserAccount
from utilities.models.abstract_base_model import AbstractBaseModel


class Notification(AbstractBaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_read = models.BooleanField(default=False)
    user_account = models.ForeignKey(
        UserAccount, on_delete=models.CASCADE, related_name="notifications"
    )

    def __str__(self):
        return self.title

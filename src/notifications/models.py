from django.db import models

from users.models import UserAccount
from utilities.models.abstract_base_model import AbstractBaseModel

from .helpers import chunks
from .services import send_notification


class Notification(AbstractBaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_read = models.BooleanField(default=False)
    user_account = models.ForeignKey(
        UserAccount, on_delete=models.CASCADE, related_name="notifications"
    )

    def __str__(self):
        return self.title

    def bulk_create(self, notification_objs, **kwargs):
        created_notifications = []

        for batch in chunks(notification_objs, 499):
            objs = super().bulk_create(batch, **kwargs)
            created_notifications.extend(objs)

        send_notification(created_notifications)
        return created_notifications

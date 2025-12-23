from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from .services import send_notification


@receiver(post_save, sender=Notification)
def send_notification_for_user(sender, instance, created, **kwargs):
    if created:
        send_notification([instance], )

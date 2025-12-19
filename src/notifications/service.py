from notifications.models import Notification

def send_notification(user_id, title, description):
    Notification.objects.create(
        title=title,
        description=description,
        user_account_id=user_id,
    )

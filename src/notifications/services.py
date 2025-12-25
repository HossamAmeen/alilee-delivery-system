from firebase_admin import messaging

from .helpers import chunks
from .models import Notification

BATCH_SIZE = 500


def send_notification_to_firebase(notification_ids):
    notifications = (
        Notification.objects.filter(id__in=notification_ids)
        .select_related("user_account")
        .prefetch_related("user_account__firebase_devices")
    )
    for notification in notifications:
        tokens = list(
            notification.user_account.firebase_devices.all().values_list(
                "token", flat=True
            )
        )

    if not tokens:
        return

    notif = messaging.Notification(
        title=notification.title,
        body=notification.description,
    )

    if len(tokens) > 1:  # Use bulk send

        for token_batch in chunks(tokens, BATCH_SIZE):
            message = messaging.MulticastMessage(notification=notif, tokens=token_batch)
            response = messaging.send_each_for_multicast(message)

            #  To avoid fail in silance
            if len(tokens) != response.success_count:
                failed_tokens = []
                for res in response.responses:
                    if not res.success:
                        for idx, resp in enumerate(res):
                            if not resp.success:
                                failed_tokens.append(token_batch[idx])
                                #  Needs action here in case of field tokens
    else:
        message = messaging.Message(notification=notif, token=tokens)
        response = messaging.send(message)

    for res in response.responses:
        print(res.success)


# *************************************************************
# check if the token is valid and if not reveal it from backend server

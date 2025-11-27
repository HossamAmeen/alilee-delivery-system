import django_filters

from notifications.models import Notification


class NotificationFilter(django_filters.FilterSet):
    class Meta:
        model = Notification
        fields = ["user_account"]

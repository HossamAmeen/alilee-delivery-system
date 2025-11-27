from rest_framework import viewsets

from notifications.filters import NotificationFilter
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from users.models import UserRole


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter

    def get_queryset(self):
        queryset = Notification.objects.order_by("-id")
        if self.request.user == UserRole.DRIVER:
            return queryset.filter(user_account=self.request.user)
        return queryset

from rest_framework import viewsets

from notifications.filters import NotificationFilter
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter

    def get_queryset(self):
        return Notification.objects.filter(user_account=self.request.user)

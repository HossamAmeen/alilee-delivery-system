from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from notifications.filters import NotificationFilter
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from users.models import UserRole


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter

    def get_queryset(self):
        queryset = Notification.objects.order_by("-id")
        if self.request.user.role == UserRole.DRIVER:
            return queryset.filter(user_account=self.request.user)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["unread_count"] = (
            self.get_queryset().filter(is_read=False).count()
        )
        return response

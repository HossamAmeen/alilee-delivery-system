from rest_framework.permissions import BasePermission

from users.models import UserRole


class IsDriver(BasePermission):

    def has_permission(self, request, view):
        return request.user.role == UserRole.DRIVER

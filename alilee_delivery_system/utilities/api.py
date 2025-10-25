from rest_framework.viewsets import ModelViewSet

from .mixins import InjectUserMixin


class BaseViewSet(InjectUserMixin, ModelViewSet):
    pass

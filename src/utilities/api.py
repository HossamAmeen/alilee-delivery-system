from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet

from .mixins import InjectUserMixin


class BaseViewSet(InjectUserMixin, ModelViewSet):
    pass

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "no_paginate",
                openapi.IN_QUERY,
                description="Set to true to disable pagination and return all results",
                type=openapi.TYPE_BOOLEAN,
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ManagerViewSet

router = DefaultRouter()
router.register(r'managers', ManagerViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

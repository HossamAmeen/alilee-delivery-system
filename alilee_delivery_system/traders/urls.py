from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import TraderViewSet

router = DefaultRouter()
router.register(r'traders', TraderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

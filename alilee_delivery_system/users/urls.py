from django.urls import path
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.api import UserAccountViewSet, TraderViewSet

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]


router = DefaultRouter()
router.register(r'', UserAccountViewSet, basename='users')
router.register(r'traders', TraderViewSet, basename='traders')
urlpatterns += router.urls

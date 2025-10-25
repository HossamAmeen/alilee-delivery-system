from django.urls import path
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.api import UserAccountViewSet, TraderViewSet

urlpatterns = [
    path('users/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('users/profile/', UserAccountViewSet.as_view({
    #     'get': 'get_profile',
    #     'patch': 'update_profile'
    # }), name='user-profile'),
]


router = DefaultRouter()
router.register(r'users', UserAccountViewSet, basename='users')
router.register(r'traders', TraderViewSet, basename='traders')
urlpatterns += router.urls

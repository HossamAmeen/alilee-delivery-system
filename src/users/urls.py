from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.api import TraderViewSet, UserAccountViewSet
from users.views.driver_view import DriverInsightsAPIView, DriverViewSet

urlpatterns = [
    path("users/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        "users/login/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "users/profile/",
        UserAccountViewSet.as_view({"get": "profile", "patch": "patch"}),
        name="user-profile",
    ),
    path(
        "drivers/insights/",
        DriverInsightsAPIView.as_view(),
        name="driver-insights",
    ),
]


router = DefaultRouter()
router.register(r"users", UserAccountViewSet, basename="users")
router.register(r"traders", TraderViewSet, basename="traders")
router.register(r"drivers", DriverViewSet, basename="drivers")
urlpatterns += router.urls

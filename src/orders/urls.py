from django.urls import path
from rest_framework.routers import DefaultRouter

from orders.api import (
    OrderAcceptAPIView,
    OrderDeliveryAssignAPIView,
    OrderDriverAssignAPIView,
    OrderViewSet,
)

router = DefaultRouter()
router.register(r"", OrderViewSet, basename="orders")

urlpatterns = [
    path(
        "orders/<str:tracking_number>/assign/",
        OrderDeliveryAssignAPIView.as_view(),
        name="order-assign-driver",
    ),
    path(
        "orders/assign/",
        OrderDriverAssignAPIView.as_view(),
        name="order-bulk-assign-driver",
    ),
    path(
        "accept-orders/",
        OrderAcceptAPIView.as_view(),
        name="order-accept",
    ),
]
urlpatterns += router.urls

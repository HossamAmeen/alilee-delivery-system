from django.urls import path
from rest_framework.routers import DefaultRouter

from orders.api import OrderViewSet

from .api import OrderDeliveryAssignAPIView

router = DefaultRouter()
router.register(r"", OrderViewSet, basename="orders")

urlpatterns = [
    path("orders/<str:tracking_number>/assign/", OrderDeliveryAssignAPIView.as_view(), name="order-assign-driver"),
]
urlpatterns += router.urls

from rest_framework.routers import DefaultRouter

from trader_pricing.api import TraderDeliveryZoneViewSet

router = DefaultRouter()
router.register(r"trader-delivery-zones", TraderDeliveryZoneViewSet, basename="trader-delivery-zones")
urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from geo.views import DeliveryZoneViewSet

router = DefaultRouter()
router.register(r"delivery-zones", DeliveryZoneViewSet, basename="delivery-zones")
urlpatterns = router.urls

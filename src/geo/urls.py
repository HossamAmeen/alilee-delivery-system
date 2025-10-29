from rest_framework.routers import DefaultRouter

from geo.views import CityViewSet, DeliveryZoneViewSet

router = DefaultRouter()
router.register(r"cities", CityViewSet, basename="cities")
router.register(r"delivery-zones", DeliveryZoneViewSet, basename="delivery-zones")
urlpatterns = router.urls

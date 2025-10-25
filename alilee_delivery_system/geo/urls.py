from rest_framework.routers import DefaultRouter

from geo.views import CityViewSet

router = DefaultRouter()
router.register(r"cities", CityViewSet, basename="cities")
urlpatterns = router.urls

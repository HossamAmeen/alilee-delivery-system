from rest_framework.routers import DefaultRouter

from transactions.api import TraderTransactionViewSet

router = DefaultRouter()
router.register(r'traders', TraderTransactionViewSet, basename='traders-transactions')
urlpatterns = router.urls

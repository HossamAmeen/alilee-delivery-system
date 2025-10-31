from rest_framework.routers import DefaultRouter

from transactions.api import ExpenseViewSet, TraderTransactionViewSet

router = DefaultRouter()
router.register(r"traders", TraderTransactionViewSet, basename="traders-transactions")
router.register(r"expenses", ExpenseViewSet, basename="expenses")
urlpatterns = router.urls

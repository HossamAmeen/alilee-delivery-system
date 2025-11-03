from rest_framework.routers import DefaultRouter

from transactions.api import ExpenseViewSet, UserAccountTransactionViewSet

router = DefaultRouter()
router.register(r"user", UserAccountTransactionViewSet, basename="user-transactions")
router.register(r"expenses", ExpenseViewSet, basename="expenses")
urlpatterns = router.urls

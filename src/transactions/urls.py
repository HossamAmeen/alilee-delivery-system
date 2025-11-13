from django.urls import path
from rest_framework.routers import DefaultRouter

from transactions.api import ExpenseViewSet, UserAccountTransactionViewSet
from transactions.api import FinancialInsightsApiView

router = DefaultRouter()
router.register(r"user", UserAccountTransactionViewSet, basename="user-transactions")
router.register(r"expenses", ExpenseViewSet, basename="expenses")
urlpatterns = [
    path("financial-insights/", FinancialInsightsApiView.as_view(),
         name="financial-insights"),
]

urlpatterns += router.urls
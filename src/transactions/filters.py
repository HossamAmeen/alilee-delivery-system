import django_filters
from django_filters import rest_framework as filters

from transactions.models import Expense, UserAccountTransaction


class ExpenseFilter(django_filters.FilterSet):
    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Expense
        fields = ["start_date", "end_date"]


class UserAccountTransactionFilter(django_filters.FilterSet):
    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = UserAccountTransaction
        fields = ["user_account", "transaction_type", "start_date", "end_date"]

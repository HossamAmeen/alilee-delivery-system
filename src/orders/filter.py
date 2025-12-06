import django_filters

from orders.models import Order


class OrderFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name="created__date", lookup_expr="gte"
    )
    end_date = django_filters.DateFilter(field_name="created__date", lookup_expr="lte")

    class Meta:
        model = Order
        fields = ["driver", "trader", "customer", "delivery_zone", "status"]

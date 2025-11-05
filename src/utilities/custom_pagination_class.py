from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request

        if request.query_params.get("no_paginate", "").lower() == "true":
            return queryset
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        if self.request.query_params.get("no_paginate", "").lower() == "true":
            return Response({"results": data})
        return super().get_paginated_response(data)

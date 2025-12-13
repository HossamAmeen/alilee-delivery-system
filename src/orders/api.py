from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.filter import OrderFilter
from orders.models import Order, OrderStatus
from orders.permissions import IsDriverPermission
from orders.serializers import (
    OrderListSerializer,
    OrderRetrieveSerializer,
    OrderSerializer,
    OrderTrackingNumberSerializer,
)
from orders.services import DeliveryAssignmentService
from users.models import Driver, UserRole
from utilities.api import BaseViewSet
from utilities.exceptions import CustomValidationError


class OrderViewSet(BaseViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OrderFilter
    search_fields = [
        "tracking_number",
        "reference_code",
        "customer__name",
        "customer__phone",
        "trader__full_name",
        "trader__email",
        "trader__phone_number",
        "driver__full_name",
        "driver__email",
        "driver__phone_number",
    ]
    ordering_fields = [
        "tracking_number",
        "reference_code",
        "created",
        "modified",
    ]
    ordering = ["-id"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

        user = self.request.user

        self.queryset = Order.objects.select_related(
            "driver", "trader", "customer", "delivery_zone"
        )

        if user.role == UserRole.DRIVER:
            return self.queryset.filter(driver=user)

        elif user.role == UserRole.TRADER:
            return self.queryset.filter(trader=user)

        return self.queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderRetrieveSerializer
        elif self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "driver",
                openapi.IN_QUERY,
                description="Filter by driver ID",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "trader",
                openapi.IN_QUERY,
                description="Filter by trader ID",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "customer",
                openapi.IN_QUERY,
                description="Filter by customer ID",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "delivery_zone",
                openapi.IN_QUERY,
                description="Filter by delivery zone ID",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description=f"Filter by order status valid values: {', '.join([status.value for status in OrderStatus])}",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Filter by start date format YYYY-MM-DD",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="Filter by end date format YYYY-MM-DD",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search in tracking number, reference code, or user details",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Which field to use when ordering the results. Prefix with - for descending order.",
                type=openapi.TYPE_STRING,
                enum=[
                    "tracking_number",
                    "-tracking_number",
                    "reference_code",
                    "-reference_code",
                    "created",
                    "-created",
                    "modified",
                    "-modified",
                ],
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderDeliveryAssignAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriverPermission]

    def patch(self, request, tracking_number):
        driver = Driver.objects.get(id=request.user.id)
        order = Order.objects.get(tracking_number=tracking_number)

        updated_order = DeliveryAssignmentService.assign_driver(order, driver)

        return Response(
            {
                "tracking_number": updated_order.tracking_number,
                "assigned_driver": driver.full_name,
                "status": updated_order.status,
            },
            status=status.HTTP_200_OK,
        )


class OrderDriverAssignAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = OrderTrackingNumberSerializer

    @swagger_auto_schema(
        operation_description="Assign multiple orders to the authenticated driver",
        request_body=OrderTrackingNumberSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "tracking_number": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Tracking number of the order",
                        ),
                        "assigned_driver": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Full name of the assigned driver",
                        ),
                        "status": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Current status of the order",
                        ),
                    },
                ),
            ),
            400: "Bad Request",
        },
    )
    def patch(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        driver = Driver.objects.get(id=serializer.validated_data.get("driver", None))

        orders = Order.objects.filter(
            tracking_number__in=serializer.validated_data["tracking_numbers"],
            driver__isnull=True,
        )

        if not orders:
            raise CustomValidationError(message="No orders available for assignment.")
        if orders.count() != len(serializer.validated_data["tracking_numbers"]):
            raise CustomValidationError(
                message="One or more orders cannot be assigned."
            )
        response_data = {
            "data": [
                {
                    "tracking_number": order.tracking_number,
                    "assigned_driver": driver.full_name,
                    "status": order.status,
                }
                for order in orders
            ]
        }

        orders.update(driver=driver, status=OrderStatus.ASSIGNED)

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )

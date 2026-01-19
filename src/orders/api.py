from orders.models import ProductPaymentStatus
import csv
from datetime import date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.service import send_notification
from orders.filter import OrderFilter
from orders.models import Order, OrderStatus
from orders.permissions import IsDriverPermission
from orders.serializers import (
    OrderListSerializer,
    OrderRetrieveSerializer,
    OrderSerializer,
    OrderTrackingNumberSerializer,
    ReferenceCodeSerializer,
)
from orders.services import DeliveryAssignmentService
from transactions.helpers import roll_back_order_transactions
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

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_status = instance.status
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if old_status != serializer.validated_data.get("status", instance.status):
            if old_status in [
                OrderStatus.DELIVERED,
                OrderStatus.POSTPONED,
                OrderStatus.CANCELLED,
            ]:
                roll_back_order_transactions(instance.id)
        self.perform_update(serializer)

        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "trader",
                openapi.IN_QUERY,
                description="Filter by trader ID",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "driver",
                openapi.IN_QUERY,
                description="Filter by driver ID",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Comma-separated order statuses example: ?status=ASSIGNED,DELIVERED",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "tracking_numbers",
                openapi.IN_QUERY,
                description="Comma-separated tracking numbers example: ?tracking_numbers=TRK1,TRK2,TRK3",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "reference_codes",
                openapi.IN_QUERY,
                description="Comma-separated reference codes example: ?reference_codes=REF1,REF2,REF3",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "date_from",
                openapi.IN_QUERY,
                description="Filter by start date format YYYY-MM-DD",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "date_to",
                openapi.IN_QUERY,
                description="Filter by end date format YYYY-MM-DD",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request, *args, **kwargs):
        queryset = Order.objects.select_related(
            "driver", "trader", "customer", "delivery_zone"
        ).order_by("-id")

        trader_id = request.query_params.get("trader")
        tracking_numbers = request.query_params.get("tracking_numbers")
        reference_codes = request.query_params.get("reference_codes")
        status = request.query_params.get("status")
        driver_id = request.query_params.get("driver")
        today = date.today()
        date_from = request.query_params.get("date_from")
        if not date_from:
            date_from = today - timedelta(days=7)
        else:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            except ValueError:
                raise CustomValidationError(
                    message="Invalid date format. Use YYYY-MM-DD."
                )
        date_to = request.query_params.get("date_to")
        if not date_to:
            date_to = today
        else:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
            except ValueError:
                raise CustomValidationError(
                    message="Invalid date format. Use YYYY-MM-DD."
                )

        if date_from:
            try:
                queryset = queryset.filter(created__date__gte=date_from)
            except (ValueError, ValidationError):
                raise CustomValidationError(
                    message="Invalid date format. Use YYYY-MM-DD."
                )

        if date_to:
            if date_from:
                if date_from > date_to:
                    raise CustomValidationError(
                        message="Date from cannot be greater than date to."
                    )

                try:
                    if (date_to - date_from).days > 7:
                        raise CustomValidationError(
                            message="Date range cannot exceed 7 days."
                        )
                except ValueError:
                    raise CustomValidationError(
                        message="Invalid date format. Use YYYY-MM-DD."
                    )

            try:
                queryset = queryset.filter(created__date__lte=date_to)
            except (ValueError, ValidationError):
                raise CustomValidationError(
                    message="Invalid date format. Use YYYY-MM-DD."
                )

        if trader_id:
            queryset = queryset.filter(trader_id=trader_id)

        if tracking_numbers:
            tracking_numbers_list = [tn.strip() for tn in tracking_numbers.split(",")]
            queryset = queryset.filter(tracking_number__in=tracking_numbers_list)

        if reference_codes:
            reference_codes_list = [rc.strip() for rc in reference_codes.split(",")]
            queryset = queryset.filter(reference_code__in=reference_codes_list)

        if status:
            status_list = [s.strip() for s in status.split(",")]
            queryset = queryset.filter(status__in=status_list)

        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)

        if queryset.count() > 5000:
            raise CustomValidationError(
                message="Cannot export more than 5000 orders at once."
            )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders_export.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "تاريخ الاضافة",
                "رقم التتبع",
                "رمز المرجع",
                "اسم التاجر",
                "العنوان",
                "الحالة",
                "عمولة المكتب"
                "فلوس للتاجر",
            ]
        )

        for order in queryset:
            trader_commission = 0
            trader_cost = order.trader_cost if order.trader_cost else order.trader_merchant_cost
            if order.product_payment_status == ProductPaymentStatus.PAID:
                trader_commission = trader_cost

            if order.product_payment_status == ProductPaymentStatus.COD:
                if order.status == OrderStatus.DELIVERED:
                    trader_commission = abs(trader_cost - order.product_cost)

            writer.writerow(
                [
                    order.created.strftime("%Y-%m-%d %H:%M:%S"),
                    order.tracking_number,
                    order.reference_code,
                    order.trader.full_name if order.trader else "",
                    order.delivery_zone.name if order.delivery_zone else "",
                    order.status_ar,
                    (
                        order.trader_cost
                        if order.trader_cost
                        else order.trader_merchant_cost
                    ),
                    order.trader_merchant_cost,
                    trader_commission,
                ]
            )

        return response


class OrderDeliveryAssignAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriverPermission]

    def patch(self, request, tracking_number):
        driver = Driver.objects.get(id=request.user.id)
        order = Order.objects.get(tracking_number=tracking_number)

        updated_order = DeliveryAssignmentService.assign_driver(order, driver)
        send_notification(
            user_id=driver.id,
            title="تم تعيينك كسائق للطلب رقم " + order.tracking_number,
            description="تم تعيينك كسائق للطلب رقم " + order.tracking_number,
        )

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
        orders.update(driver=driver, status=OrderStatus.ASSIGNED)

        data = []
        for tracking_number in serializer.validated_data["tracking_numbers"]:
            send_notification(
                user_id=driver.id,
                title="تم تعيينك كسائق للطلب رقم " + tracking_number,
                description="تم تعيينك كسائق للطلب رقم " + tracking_number,
            )
            data.append(
                {
                    "tracking_number": tracking_number,
                    "assigned_driver": driver.full_name,
                    "status": OrderStatus.ASSIGNED,
                }
            )

        return Response(
            data,
            status=status.HTTP_200_OK,
        )


class OrderAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriverPermission]

    @swagger_auto_schema(
        operation_description="Accept multiple orders for the authenticated driver",
        request_body=ReferenceCodeSerializer,
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
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                    "errors": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "tracking_number": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "message": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    ),
                },
            ),
        },
    )
    def post(self, request):
        serializer = ReferenceCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        driver = Driver.objects.filter(id=request.user.id).first()
        if not driver:
            raise CustomValidationError(message="Driver not found.")
        orders = Order.objects.filter(
            reference_code__in=serializer.validated_data["reference_codes"]
        )
        errors = []
        if not orders:
            raise CustomValidationError(
                message="لا توجد طلبات بهذه اكواد التعريفة", errors=errors
            )
        if orders.count() != len(serializer.validated_data["reference_codes"]):
            orders_reference_codes = orders.values_list("reference_code", flat=True)
            for reference_code in serializer.validated_data["reference_codes"]:
                if reference_code not in orders_reference_codes:
                    errors.append(
                        {reference_code: f"هذا الطلب {reference_code} غير موجود."}
                    )

        for order in orders:
            if order.driver:
                errors.append(
                    {
                        order.reference_code: f"هذا الطلب {order.reference_code} مخصص ل{order.driver.full_name}."
                    }
                )
            elif order.status not in [OrderStatus.CREATED, OrderStatus.IN_PROGRESS]:
                errors.append(
                    {
                        order.reference_code: f"هذا الطلب {order.reference_code} غير قابل للقبول لأنه {order.status}."
                    }
                )

        if errors:
            raise CustomValidationError(
                message="بعض الطلبات غير قابلة للقبول", errors=errors
            )

        response_data = {
            "data": [
                {
                    "reference_code": order.reference_code,
                    "assigned_driver": driver.full_name,
                }
                for order in orders
            ]
        }

        orders.update(driver=driver, status=OrderStatus.ASSIGNED)

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )

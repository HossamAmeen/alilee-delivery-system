from django.core.exceptions import ValidationError


class DeliveryAssignmentService:
    @staticmethod
    def assign_driver(order, driver):
        forbidden_statuses = ["DELIVERED", "CANCELLED"]
        if order.driver or order.status in forbidden_statuses:
            raise ValidationError("Order is already assigned to a driver or "
                  "cannot be assigned due to its status.")

        order.driver = driver
        order.status = "ASSIGNED"
        order.save()

        return order

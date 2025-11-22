from utilities.exceptions import CustomValidationError


class DeliveryAssignmentService:
    @staticmethod
    def assign_driver(order, driver):
        forbidden_statuses = ["DELIVERED", "CANCELLED", "ASSIGNED"]
        if order.driver :
            raise CustomValidationError(
                "Order is already assigned to a driver.")
        if order.status in forbidden_statuses:
            raise CustomValidationError(
                "Order cannot be assigned due to its status.")
        order.driver = driver
        order.status = "ASSIGNED"
        order.save()

        return order

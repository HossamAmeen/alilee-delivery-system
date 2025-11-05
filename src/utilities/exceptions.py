from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import PermissionDenied, exception_handler


class CustomValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "validation_error"

    def __init__(
        self, message="Validation failed", code=None, errors=None, status_code=None
    ):
        if status_code is not None:
            self.status_code = status_code

        detail = {
            "code": code or self.default_code,
            "message": message,
            "errors": errors or [],
        }
        super().__init__(detail=detail)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, CustomValidationError):
        # Already formatted in the exception
        return response

    if response is not None and isinstance(exc, ValidationError):
        # Format other validation errors
        formatted_errors = []
        for field, errors in response.data.items():
            if isinstance(errors, dict):
                errors = errors.values()

            for error in errors:
                formatted_errors.append({"field": field, "message": str(error)})

        response.data = {
            "code": "validation_error",
            "message": "Validation failed",
            "errors": formatted_errors,
        }
    elif response is not None and isinstance(exc, PermissionDenied):
        response.data = {
            "code": "permission_denied",
            "message": response.data["detail"],
            "errors": [],
        }

    return response

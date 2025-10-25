from rest_framework.exceptions import ValidationError
from rest_framework.views import PermissionDenied, exception_handler

from .base_exception_class import CustomValidationError


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    print("test" * 50)

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

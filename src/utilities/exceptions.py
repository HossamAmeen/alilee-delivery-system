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

    if response is None:
        return response

    # Already formatted manually
    if isinstance(exc, CustomValidationError):
        return response

    # Handle DRF ValidationError
    if isinstance(exc, ValidationError):
        formatted_errors = []
        main_message = "Validation failed"

        for field, errors in response.data.items():
            # Handle nested dict errors
            if isinstance(errors, dict):
                errors = errors.values()

            for error in errors:
                error_message = str(error)

                formatted_errors.append(
                    {
                        "field": field,
                        "message": error_message,
                    }
                )

                # Take FIRST error as main message
                if main_message == "Validation failed":
                    print("ERROR MESSAGE:", error_message)
                    main_message = error_message

        response.data = {
            "code": "validation_error",
            "message": main_message,
            "errors": formatted_errors,
        }

    elif isinstance(exc, PermissionDenied):
        response.data = {
            "code": "permission_denied",
            "message": response.data.get("detail"),
            "errors": [],
        }

    return response

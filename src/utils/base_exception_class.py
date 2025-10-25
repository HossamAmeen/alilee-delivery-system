from rest_framework import status
from rest_framework.exceptions import APIException


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

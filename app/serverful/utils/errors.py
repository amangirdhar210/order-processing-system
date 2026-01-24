from typing import Dict, Optional
from fastapi import status


class ErrorCode:
    INVALID_CREDENTIALS = 1001
    UNAUTHORIZED = 1002
    TOKEN_EXPIRED = 1003
    INVALID_TOKEN = 1004
    INSUFFICIENT_PERMISSIONS = 1005

    USER_NOT_FOUND = 2001
    USER_ALREADY_EXISTS = 2002

    ORDER_NOT_FOUND = 3001
    INVALID_ORDER_STATUS = 3004
    ORDER_CANNOT_BE_CANCELLED = 3008

    PAYMENT_FAILED = 4001
    PAYMENT_PROCESSING_ERROR = 4002

    INVALID_INPUT = 5001

    INTERNAL_ERROR = 9001


ERROR_REGISTRY: Dict[int, Dict[str, any]] = {
    ErrorCode.INVALID_CREDENTIALS: {
        "message": "Invalid email or password",
        "status_code": status.HTTP_401_UNAUTHORIZED,
    },
    ErrorCode.UNAUTHORIZED: {
        "message": "Unauthorized access",
        "status_code": status.HTTP_401_UNAUTHORIZED,
    },
    ErrorCode.TOKEN_EXPIRED: {
        "message": "Authentication token has expired",
        "status_code": status.HTTP_401_UNAUTHORIZED,
    },
    ErrorCode.INVALID_TOKEN: {
        "message": "Invalid authentication token",
        "status_code": status.HTTP_401_UNAUTHORIZED,
    },
    ErrorCode.INSUFFICIENT_PERMISSIONS: {
        "message": "Insufficient permissions to perform this action",
        "status_code": status.HTTP_403_FORBIDDEN,
    },
    ErrorCode.USER_NOT_FOUND: {
        "message": "User not found",
        "status_code": status.HTTP_404_NOT_FOUND,
    },
    ErrorCode.USER_ALREADY_EXISTS: {
        "message": "User with this email already exists",
        "status_code": status.HTTP_409_CONFLICT,
    },
    ErrorCode.ORDER_NOT_FOUND: {
        "message": "Order not found",
        "status_code": status.HTTP_404_NOT_FOUND,
    },
    ErrorCode.INVALID_ORDER_STATUS: {
        "message": "Invalid order status",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.ORDER_CANNOT_BE_CANCELLED: {
        "message": "Order cannot be cancelled in current status",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.PAYMENT_FAILED: {
        "message": "Payment processing failed",
        "status_code": status.HTTP_402_PAYMENT_REQUIRED,
    },
    ErrorCode.PAYMENT_PROCESSING_ERROR: {
        "message": "Error processing payment",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    },
    ErrorCode.INVALID_INPUT: {
        "message": "Invalid input provided",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.INTERNAL_ERROR: {
        "message": "Internal server error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    },
}


class ApplicationError(Exception):
    def __init__(
        self,
        error_code: int,
        message: Optional[str] = None,
        details: Optional[str] = None,
    ):
        self.error_code = error_code
        error_info = ERROR_REGISTRY.get(error_code, {})
        self.message = message or error_info.get("message", "Unknown error")
        self.status_code = error_info.get("status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> Dict:
        response = {
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details:
            response["details"] = self.details
        return response

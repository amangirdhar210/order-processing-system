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
    INVALID_EMAIL = 2003
    INVALID_USER_DATA = 2004

    ORDER_NOT_FOUND = 3001
    ORDER_CONFLICT = 3002
    INVALID_ORDER_DATA = 3003
    INVALID_ORDER_STATUS = 3004
    INVALID_STATE_TRANSITION = 3005
    ORDER_ITEMS_EMPTY = 3006
    INVALID_ORDER_TOTAL = 3007

    PAYMENT_FAILED = 4001
    PAYMENT_PROCESSING_ERROR = 4002
    INVALID_PAYMENT_METHOD = 4003

    INVALID_INPUT = 5001
    MISSING_REQUIRED_FIELD = 5002
    INVALID_FORMAT = 5003

    INTERNAL_ERROR = 9001
    DATABASE_ERROR = 9002
    EXTERNAL_SERVICE_ERROR = 9003
    SQS_ERROR = 9004


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
    ErrorCode.INVALID_EMAIL: {
        "message": "Invalid email format",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.INVALID_USER_DATA: {
        "message": "Invalid user data provided",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.ORDER_NOT_FOUND: {
        "message": "Order not found",
        "status_code": status.HTTP_404_NOT_FOUND,
    },
    ErrorCode.ORDER_CONFLICT: {
        "message": "Order state conflict - concurrent modification detected",
        "status_code": status.HTTP_409_CONFLICT,
    },
    ErrorCode.INVALID_ORDER_DATA: {
        "message": "Invalid order data provided",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.INVALID_ORDER_STATUS: {
        "message": "Invalid order status",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.INVALID_STATE_TRANSITION: {
        "message": "Invalid order status transition",
        "status_code": status.HTTP_409_CONFLICT,
    },
    ErrorCode.ORDER_ITEMS_EMPTY: {
        "message": "Order must contain at least one item",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.INVALID_ORDER_TOTAL: {
        "message": "Order total does not match sum of items",
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
    ErrorCode.INVALID_PAYMENT_METHOD: {
        "message": "Invalid payment method",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.INVALID_INPUT: {
        "message": "Invalid input provided",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.MISSING_REQUIRED_FIELD: {
        "message": "Missing required field",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.INVALID_FORMAT: {
        "message": "Invalid format",
        "status_code": status.HTTP_400_BAD_REQUEST,
    },
    ErrorCode.INTERNAL_ERROR: {
        "message": "Internal server error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    },
    ErrorCode.DATABASE_ERROR: {
        "message": "Database operation failed",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
    },
    ErrorCode.EXTERNAL_SERVICE_ERROR: {
        "message": "External service error",
        "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
    },
    ErrorCode.SQS_ERROR: {
        "message": "Failed to send notification to queue",
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

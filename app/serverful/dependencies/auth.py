from fastapi import Header, Request
from typing import Optional
from app.serverful.utils.jwt_utils import validate_token
from app.serverful.utils.errors import ApplicationError, ErrorCode


def verify_token(request: Request, authorization: Optional[str] = Header(None)) -> None:
    if not authorization:
        raise ApplicationError(ErrorCode.UNAUTHORIZED, details="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise ApplicationError(ErrorCode.INVALID_TOKEN, details="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    
    payload = validate_token(token)
    
    if not payload:
        raise ApplicationError(ErrorCode.INVALID_TOKEN, details="Invalid or expired token")
    
    user_id = payload.get("user_id")
    user_name = payload.get("user_name")
    role = payload.get("role")
    
    if not user_id or not user_name or not role:
        raise ApplicationError(ErrorCode.INVALID_TOKEN, details="Invalid token payload")
    
    request.state.current_user = {
        "user_id": user_id,
        "user_name": user_name,
        "role": role
    }


def require_user(request: Request, authorization: Optional[str] = Header(None)) -> None:
    verify_token(request, authorization)
    
    role = request.state.current_user.get("role")
    
    if role not in ["user"]:
        raise ApplicationError(ErrorCode.INSUFFICIENT_PERMISSIONS, details="Invalid role")


def require_staff(request: Request, authorization: Optional[str] = Header(None)) -> None:
    verify_token(request, authorization)
    
    role = request.state.current_user.get("role")
    
    if role not in ["staff", "admin"]:
        raise ApplicationError(ErrorCode.INSUFFICIENT_PERMISSIONS, details="Staff or admin access required")


def require_admin(request: Request, authorization: Optional[str] = Header(None)) -> None:
    verify_token(request, authorization)
    
    role = request.state.current_user.get("role")
    
    if role != "admin":
        raise ApplicationError(ErrorCode.INSUFFICIENT_PERMISSIONS, details="Admin access required")


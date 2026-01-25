import pytest
from fastapi import Request, HTTPException
from unittest.mock import Mock
from app.serverful.dependencies.auth import verify_token, require_user, require_staff, require_admin
from app.serverful.utils.jwt_utils import generate_token
from app.serverful.utils.errors import ApplicationError, ErrorCode


class TestVerifyToken:
    def test_verify_token_success(self):
        request = Mock(spec=Request)
        token = generate_token("user123", "John Doe", "user")
        authorization = f"Bearer {token}"
        
        verify_token(request, authorization)
        
        assert request.state.current_user["user_id"] == "user123"
        assert request.state.current_user["user_name"] == "John Doe"
        assert request.state.current_user["role"] == "user"

    def test_verify_token_missing_authorization_header(self):
        request = Mock(spec=Request)
        
        with pytest.raises(ApplicationError) as exc_info:
            verify_token(request, None)
        
        assert exc_info.value.error_code == ErrorCode.UNAUTHORIZED
        assert "Authorization header missing" in exc_info.value.details

    def test_verify_token_invalid_header_format(self):
        request = Mock(spec=Request)
        token = generate_token("user123", "John Doe", "user")
        
        with pytest.raises(ApplicationError) as exc_info:
            verify_token(request, token)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TOKEN
        assert "Invalid authorization header format" in exc_info.value.details

    def test_verify_token_invalid_token(self):
        request = Mock(spec=Request)
        
        with pytest.raises(ApplicationError) as exc_info:
            verify_token(request, "Bearer invalid.token.here")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TOKEN

    def test_verify_token_expired_token(self):
        request = Mock(spec=Request)
        
        import jwt
        from datetime import datetime, timedelta, timezone
        from app.serverful.config.config import settings
        
        expired_payload = {
            "user_id": "user123",
            "user_name": "John Doe",
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        with pytest.raises(ApplicationError) as exc_info:
            verify_token(request, f"Bearer {expired_token}")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TOKEN

    def test_verify_token_missing_user_id_in_payload(self):
        request = Mock(spec=Request)
        
        import jwt
        from datetime import datetime, timedelta, timezone
        from app.serverful.config.config import settings
        
        invalid_payload = {
            "user_name": "John Doe",
            "role": "user",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        invalid_token = jwt.encode(invalid_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        with pytest.raises(ApplicationError) as exc_info:
            verify_token(request, f"Bearer {invalid_token}")
        
        assert exc_info.value.error_code == ErrorCode.INVALID_TOKEN
        assert "Invalid token payload" in exc_info.value.details


class TestRequireUser:
    def test_require_user_valid_user_role(self):
        request = Mock(spec=Request)
        token = generate_token("user123", "John Doe", "user")
        
        require_user(request, f"Bearer {token}")
        
        assert request.state.current_user["role"] == "user"

    def test_require_user_staff_role_denied(self):
        request = Mock(spec=Request)
        token = generate_token("staff123", "Staff User", "staff")
        
        with pytest.raises(ApplicationError) as exc_info:
            require_user(request, f"Bearer {token}")
        
        assert exc_info.value.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS


class TestRequireStaff:
    def test_require_staff_valid_staff_role(self):
        request = Mock(spec=Request)
        token = generate_token("staff123", "Staff User", "staff")
        
        require_staff(request, f"Bearer {token}")
        
        assert request.state.current_user["role"] == "staff"

    def test_require_staff_valid_admin_role(self):
        request = Mock(spec=Request)
        token = generate_token("admin123", "Admin User", "admin")
        
        require_staff(request, f"Bearer {token}")
        
        assert request.state.current_user["role"] == "admin"


class TestRequireAdmin:
    def test_require_admin_valid_admin_role(self):
        request = Mock(spec=Request)
        token = generate_token("admin123", "Admin User", "admin")
        
        require_admin(request, f"Bearer {token}")
        
        assert request.state.current_user["role"] == "admin"

    def test_require_admin_staff_role_denied(self):
        request = Mock(spec=Request)
        token = generate_token("staff123", "Staff User", "staff")
        
        with pytest.raises(ApplicationError) as exc_info:
            require_admin(request, f"Bearer {token}")
        
        assert exc_info.value.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS

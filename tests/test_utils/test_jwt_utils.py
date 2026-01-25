import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import jwt
from app.serverful.utils.jwt_utils import generate_token, validate_token
from app.serverful.config.config import settings


class TestGenerateToken:
    def test_generate_token_success(self):
        token = generate_token("user123", "John Doe", "user")
        
        assert token is not None
        assert isinstance(token, str)
        
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["user_id"] == "user123"
        assert payload["user_name"] == "John Doe"
        assert payload["role"] == "user"
        assert "exp" in payload
        assert "iat" in payload

    def test_generate_token_with_admin_role(self):
        token = generate_token("admin123", "Admin User", "admin")
        
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["role"] == "admin"

    def test_generate_token_with_staff_role(self):
        token = generate_token("staff123", "Staff User", "staff")
        
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["role"] == "staff"


class TestValidateToken:
    def test_validate_token_success(self):
        token = generate_token("user123", "John Doe", "user")
        
        payload = validate_token(token)
        
        assert payload is not None
        assert payload["user_id"] == "user123"
        assert payload["user_name"] == "John Doe"
        assert payload["role"] == "user"

    def test_validate_token_expired(self):
        expired_payload = {
            "user_id": "user123",
            "user_name": "John Doe",
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        payload = validate_token(expired_token)
        
        assert payload is None

    def test_validate_token_invalid_signature(self):
        token = generate_token("user123", "John Doe", "user")
        tampered_token = token[:-10] + "tampered!"
        
        payload = validate_token(tampered_token)
        
        assert payload is None

    def test_validate_token_malformed(self):
        invalid_token = "not.a.valid.jwt.token"
        
        payload = validate_token(invalid_token)
        
        assert payload is None

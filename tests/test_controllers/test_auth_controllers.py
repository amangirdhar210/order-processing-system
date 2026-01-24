import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.serverful.models.models import User
from app.serverful.utils.errors import ApplicationError, ErrorCode


class TestAuthControllers:

    @pytest.fixture(scope="class")
    def mock_auth_service(self):
        return MagicMock()

    @pytest.fixture(scope="class")
    def mock_user_service(self):
        return MagicMock()

    @pytest.fixture(scope="class")
    def client(self, mock_auth_service, mock_user_service):
        from fastapi import FastAPI
        from app.serverful.controllers.auth_controllers import auth_router
        from app.serverful.dependencies.dependencies import get_auth_service, get_user_service
        from app.serverful.utils.exception_handlers import application_error_handler, general_exception_handler
        from app.serverful.utils.errors import ApplicationError

        app = FastAPI()
        app.include_router(auth_router)
        app.add_exception_handler(ApplicationError, application_error_handler)
        app.add_exception_handler(Exception, general_exception_handler)
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
        app.dependency_overrides[get_user_service] = lambda: mock_user_service

        return TestClient(app, raise_server_exceptions=False)

    @pytest.fixture
    def sample_user(self):
        return User(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="hashed_password",
            role="user",
            created_at=1704700000,
            updated_at=1704700000,
        )

    @pytest.fixture
    def valid_register_payload(self):
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "password123"
        }

    @pytest.fixture
    def valid_login_payload(self):
        return {"email": "john@example.com", "password": "password123"}

    def test_register_success(self, client, mock_user_service, valid_register_payload):
        mock_user_service.register_user = AsyncMock(return_value=None)
        response = client.post("/auth/register", json=valid_register_payload)
        assert response.status_code == 201
        assert response.json()["message"] == "User created successfully, please login"
        mock_user_service.register_user.assert_called_once()

    def test_register_duplicate_email(self, client, mock_user_service, valid_register_payload):
        mock_user_service.register_user = AsyncMock(side_effect=ApplicationError(ErrorCode.USER_ALREADY_EXISTS))
        response = client.post("/auth/register", json=valid_register_payload)
        assert response.status_code == 409

    @pytest.mark.parametrize("payload,description", [
        ({"first_name": "John", "last_name": "Doe", "password": "password123"}, "missing email"),
        ({"first_name": "John", "last_name": "Doe", "email": "john@example.com"}, "missing password"),
        ({"last_name": "Doe", "email": "john@example.com", "password": "password123"}, "missing first_name"),
        ({"first_name": "John", "email": "john@example.com", "password": "password123"}, "missing last_name"),
        ({"first_name": "J", "last_name": "Doe", "email": "john@example.com", "password": "password123"}, "first_name too short"),
        ({"first_name": "John", "last_name": "D", "email": "john@example.com", "password": "password123"}, "last_name too short"),
        ({"first_name": "John", "last_name": "Doe", "email": "invalid-email", "password": "password123"}, "invalid email format"),
        ({"first_name": "John", "last_name": "Doe", "email": "john@example.com", "password": "short"}, "password too short"),
        ({}, "empty payload"),
    ])
    def test_register_validation_errors(self, client, payload, description):
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 422, f"Failed for case: {description}"

    def test_login_success(self, client, mock_auth_service, sample_user, valid_login_payload):
        mock_auth_service.login_user = AsyncMock(return_value={
            "token": "mock-jwt-token",
            "user": {"id": sample_user.user_id, "first_name": sample_user.first_name, 
                     "last_name": sample_user.last_name, "email": sample_user.email, "role": sample_user.role}
        })
        response = client.post("/auth/login", json=valid_login_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "mock-jwt-token"
        assert data["user"]["id"] == sample_user.user_id
        assert "password" not in data["user"]
        mock_auth_service.login_user.assert_called_once()

    def test_login_invalid_credentials(self, client, mock_auth_service, valid_login_payload):
        mock_auth_service.login_user = AsyncMock(side_effect=ApplicationError(ErrorCode.INVALID_CREDENTIALS))
        response = client.post("/auth/login", json=valid_login_payload)
        assert response.status_code == 401

    @pytest.mark.parametrize("payload,description", [
        ({"password": "password123"}, "missing email"),
        ({"email": "john@example.com"}, "missing password"),
        ({"email": "not-an-email", "password": "password123"}, "invalid email format"),
        ({"email": "  ", "password": "  "}, "empty credentials"),
        ({}, "empty payload"),
        ({"email": "", "password": "password123"}, "empty email"),
        ({"email": "john@example.com", "password": "short"}, "password too short"),
    ])
    def test_login_validation_errors(self, client, payload, description):
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 422, f"Failed for case: {description}"

    def test_login_service_error(self, client, mock_auth_service, valid_login_payload):
        mock_auth_service.login_user = AsyncMock(side_effect=Exception("Database error"))
        response = client.post("/auth/login", json=valid_login_payload)
        assert response.status_code == 500

    def test_login_admin_user(self, client, mock_auth_service, valid_login_payload):
        mock_auth_service.login_user = AsyncMock(return_value={
            "token": "admin-jwt-token",
            "user": {"id": "223e4567-e89b-12d3-a456-426614174000", "first_name": "Admin", 
                     "last_name": "User", "email": "admin@example.com", "role": "admin"}
        })
        response = client.post("/auth/login", json=valid_login_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "admin-jwt-token"
        assert data["user"]["role"] == "admin"

    def test_register_service_error(self, client, mock_user_service, valid_register_payload):
        mock_user_service.register_user = AsyncMock(side_effect=Exception("Database error"))
        response = client.post("/auth/register", json=valid_register_payload)
        assert response.status_code == 500

    def test_login_response_structure(self, client, mock_auth_service, valid_login_payload):
        mock_auth_service.login_user = AsyncMock(return_value={
            "token": "test-token",
            "user": {"id": "323e4567-e89b-12d3-a456-426614174000", "first_name": "Test", 
                     "last_name": "User", "email": "test@example.com", "role": "user"}
        })
        response = client.post("/auth/login", json=valid_login_payload)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data and "user" in data
        assert all(key in data["user"] for key in ["id", "first_name", "last_name", "email", "role"])

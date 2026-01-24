import pytest
from unittest.mock import AsyncMock
from app.serverful.services.auth_service import AuthService
from app.serverful.models.models import User
from app.serverful.models.dto import LoginUserRequest
from app.serverful.utils.errors import ApplicationError, ErrorCode


class TestAuthService:

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def auth_service(self, mock_user_repo):
        return AuthService(mock_user_repo)

    @pytest.fixture
    def sample_user(self):
        from app.serverful.utils import password_utils

        return User(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            password=password_utils.hash_password("correct_password"),
            first_name="Test",
            last_name="User",
            created_at=1704067200,
            updated_at=1704067200,
        )

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user_repo, sample_user):
        mock_user_repo.get_by_email.return_value = sample_user
        login_request = LoginUserRequest(email="test@example.com", password="correct_password")

        result = await auth_service.login_user(login_request)

        assert result is not None
        assert "token" in result
        assert "user" in result
        assert isinstance(result["token"], str)
        assert result["user"]["id"] == sample_user.user_id
        assert result["user"]["email"] == sample_user.email
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")

    @pytest.mark.asyncio
    async def test_login_email_not_found(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None
        login_request = LoginUserRequest(email="nonexistent@example.com", password="password")

        with pytest.raises(ApplicationError) as exc_info:
            await auth_service.login_user(login_request)
        assert exc_info.value.error_code == ErrorCode.INVALID_CREDENTIALS

    @pytest.mark.asyncio
    async def test_login_incorrect_password(
        self, auth_service, mock_user_repo, sample_user
    ):
        mock_user_repo.get_by_email.return_value = sample_user
        login_request = LoginUserRequest(email="test@example.com", password="wrong_password")

        with pytest.raises(ApplicationError) as exc_info:
            await auth_service.login_user(login_request)
        assert exc_info.value.error_code == ErrorCode.INVALID_CREDENTIALS



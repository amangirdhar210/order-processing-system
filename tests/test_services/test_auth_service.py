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
            first_name="John",
            last_name="Doe",
            email="test@example.com",
            password=password_utils.hash_password("correct_password"),
            role="user",
            created_at=1704067200,
            updated_at=1704067200,
        )

    @pytest.fixture
    def login_request(self):
        return LoginUserRequest(email="test@example.com", password="correct_password")

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user_repo, sample_user, login_request):
        mock_user_repo.get_by_email.return_value = sample_user
        result = await auth_service.login_user(login_request)
        assert "token" in result and "user" in result
        assert isinstance(result["token"], str)
        assert result["user"]["id"] == sample_user.user_id
        assert "password" not in result["user"]

    @pytest.mark.asyncio
    async def test_login_email_not_found(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None
        with pytest.raises(ApplicationError) as exc_info:
            await auth_service.login_user(LoginUserRequest(email="nonexistent@example.com", password="password"))
        assert exc_info.value.error_code == ErrorCode.INVALID_CREDENTIALS

    @pytest.mark.asyncio
    async def test_login_incorrect_password(self, auth_service, mock_user_repo, sample_user):
        mock_user_repo.get_by_email.return_value = sample_user
        with pytest.raises(ApplicationError) as exc_info:
            await auth_service.login_user(LoginUserRequest(email="test@example.com", password="wrong_password"))
        assert exc_info.value.error_code == ErrorCode.INVALID_CREDENTIALS

    @pytest.mark.asyncio
    async def test_login_returns_correct_user_data(self, auth_service, mock_user_repo, sample_user, login_request):
        mock_user_repo.get_by_email.return_value = sample_user
        result = await auth_service.login_user(login_request)
        user_data = result["user"]
        assert user_data["id"] == sample_user.user_id
        assert user_data["email"] == sample_user.email
        assert user_data["first_name"] == sample_user.first_name
        assert user_data["last_name"] == sample_user.last_name
        assert user_data["role"] == sample_user.role

    @pytest.mark.asyncio
    async def test_login_admin_user(self, auth_service, mock_user_repo):
        from app.serverful.utils import password_utils
        admin_user = User(
            user_id="223e4567-e89b-12d3-a456-426614174000",
            first_name="Admin", last_name="User", email="admin@example.com",
            password=password_utils.hash_password("admin_password"),
            role="admin", created_at=1704067200, updated_at=1704067200,
        )
        mock_user_repo.get_by_email.return_value = admin_user
        result = await auth_service.login_user(LoginUserRequest(email="admin@example.com", password="admin_password"))
        assert result["user"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_login_staff_user(self, auth_service, mock_user_repo):
        from app.serverful.utils import password_utils
        staff_user = User(
            user_id="323e4567-e89b-12d3-a456-426614174000",
            first_name="Staff", last_name="Member", email="staff@example.com",
            password=password_utils.hash_password("staff_password"),
            role="staff", created_at=1704067200, updated_at=1704067200,
        )
        mock_user_repo.get_by_email.return_value = staff_user
        result = await auth_service.login_user(LoginUserRequest(email="staff@example.com", password="staff_password"))
        assert result["user"]["role"] == "staff"

    @pytest.mark.asyncio
    async def test_login_token_generation(self, auth_service, mock_user_repo, sample_user, login_request):
        mock_user_repo.get_by_email.return_value = sample_user
        result = await auth_service.login_user(login_request)
        assert result["token"] is not None
        assert len(result["token"]) > 0
        assert result["token"].count(".") == 2

    @pytest.mark.asyncio
    async def test_login_password_not_exposed(self, auth_service, mock_user_repo, sample_user, login_request):
        mock_user_repo.get_by_email.return_value = sample_user
        result = await auth_service.login_user(login_request)
        assert "password" not in result
        assert "password" not in result["user"]

    @pytest.mark.asyncio
    async def test_login_repository_called_correctly(self, auth_service, mock_user_repo, sample_user, login_request):
        mock_user_repo.get_by_email.return_value = sample_user
        await auth_service.login_user(login_request)
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")

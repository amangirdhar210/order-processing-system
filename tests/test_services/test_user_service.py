import pytest
from unittest.mock import AsyncMock
from app.serverful.services.user_service import UserService
from app.serverful.models.models import User
from app.serverful.models.dto import RegisterUserRequest
from app.serverful.utils.errors import ApplicationError, ErrorCode


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def user_service(mock_user_repo):
    return UserService(mock_user_repo)


@pytest.fixture
def sample_user():
    return User(
        user_id="123e4567-e89b-12d3-a456-426614174000",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password="$2b$12$hashedpassword",
        created_at=1234567890,
        updated_at=1234567890
    )


@pytest.fixture
def register_request():
    return RegisterUserRequest(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password="password123"
    )


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_register_user_success(self, user_service, mock_user_repo, register_request):
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = None
        
        await user_service.register_user(register_request)
        
        mock_user_repo.get_by_email.assert_called_once_with(register_request.email)
        assert mock_user_repo.create.call_count == 1
        created_user = mock_user_repo.create.call_args[0][0]
        assert created_user.first_name == "John"
        assert created_user.last_name == "Doe"
        assert created_user.email == register_request.email
        assert created_user.password != "password123"

    @pytest.mark.asyncio
    async def test_register_user_already_exists(self, user_service, mock_user_repo, register_request, sample_user):
        mock_user_repo.get_by_email.return_value = sample_user
        
        with pytest.raises(ApplicationError) as exc_info:
            await user_service.register_user(register_request)
        
        assert exc_info.value.error_code == ErrorCode.USER_ALREADY_EXISTS
        mock_user_repo.create.assert_not_called()


class TestRegisterStaffUser:
    @pytest.mark.asyncio
    async def test_register_staff_user_success(self, user_service, mock_user_repo):
        from app.serverful.models.dto import CreateStaffRequest
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = None
        staff_request = CreateStaffRequest(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="adminpass",
            role="staff"
        )
        
        await user_service.register_staff_user(staff_request)
        
        mock_user_repo.get_by_email.assert_called_once_with(staff_request.email)
        assert mock_user_repo.create.call_count == 1
        created_user = mock_user_repo.create.call_args[0][0]
        assert created_user.role == "staff"
        assert created_user.email == staff_request.email

    @pytest.mark.asyncio
    async def test_register_staff_user_already_exists(self, user_service, mock_user_repo, sample_user):
        from app.serverful.models.dto import CreateStaffRequest
        mock_user_repo.get_by_email.return_value = sample_user
        staff_request = CreateStaffRequest(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="adminpass",
            role="staff"
        )
        
        with pytest.raises(ApplicationError) as exc_info:
            await user_service.register_staff_user(staff_request)
        
        assert exc_info.value.error_code == ErrorCode.USER_ALREADY_EXISTS
        mock_user_repo.create.assert_not_called()


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_user_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.delete.return_value = None
        
        await user_service.delete_user(sample_user.user_id)
        
        mock_user_repo.get_by_id.assert_called_once_with(sample_user.user_id)
        mock_user_repo.delete.assert_called_once_with(sample_user.user_id, sample_user.email)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await user_service.delete_user("123e4567-e89b-12d3-a456-426614174000")
        
        assert exc_info.value.error_code == ErrorCode.USER_NOT_FOUND
        mock_user_repo.delete.assert_not_called()


class TestGetUsers:
    @pytest.mark.asyncio
    async def test_get_all_users(self, user_service, mock_user_repo, sample_user):
        mock_user_repo.get_all.return_value = [sample_user]
        
        result = await user_service.get_all_users()
        
        assert len(result) == 1
        assert result[0] == sample_user
        mock_user_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_user_repo, sample_user):
        mock_user_repo.get_by_id.return_value = sample_user
        
        result = await user_service.get_user_by_id(sample_user.user_id)
        
        assert result == sample_user
        mock_user_repo.get_by_id.assert_called_once_with(sample_user.user_id)

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_user_repo):
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await user_service.get_user_by_id("123e4567-e89b-12d3-a456-426614174000")
        
        assert exc_info.value.error_code == ErrorCode.USER_NOT_FOUND

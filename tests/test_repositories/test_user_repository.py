import pytest
from unittest.mock import MagicMock, AsyncMock
import asyncio
from decimal import Decimal
from app.serverful.repositories.user_repository import UserRepository
from app.serverful.models.models import User


@pytest.fixture
def mock_dynamodb():
    dynamodb = MagicMock()
    table = MagicMock()
    table.table_name = "test-table"
    client = MagicMock()
    dynamodb.Table.return_value = table
    dynamodb.meta.client = client
    return dynamodb, table, client


@pytest.fixture
def user_repo(mock_dynamodb):
    dynamodb, table, client = mock_dynamodb
    return UserRepository(dynamodb, "test-table"), table, client


@pytest.fixture
def sample_user():
    return User(
        user_id="123e4567-e89b-12d3-a456-426614174000",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password="$2b$12$hashedpassword",
        role="user",
        created_at=1234567890,
        updated_at=1234567890
    )


class TestCreateUser:
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repo, sample_user):
        repo, table, client = user_repo
        client.transact_write_items.return_value = {}
        
        await repo.create(sample_user)
        
        assert client.transact_write_items.call_count == 1
        call_args = client.transact_write_items.call_args[1]
        transact_items = call_args["TransactItems"]
        assert len(transact_items) == 2
        assert transact_items[0]["Put"]["Item"]["PK"] == f"EMAIL#{sample_user.email}"
        assert transact_items[0]["Put"]["Item"]["SK"] == f"USER#{sample_user.user_id}"
        assert transact_items[1]["Put"]["Item"]["PK"] == f"USER#{sample_user.user_id}"
        assert transact_items[1]["Put"]["Item"]["SK"] == "PROFILE"


class TestGetUser:
    @pytest.mark.asyncio
    async def test_get_by_email_success(self, user_repo, sample_user):
        repo, table, client = user_repo
        table.query.return_value = {
            "Items": [{
                "user_id": sample_user.user_id,
                "first_name": sample_user.first_name,
                "last_name": sample_user.last_name,
                "email": sample_user.email,
                "password": sample_user.password,
                "role": sample_user.role,
                "created_at": sample_user.created_at,
                "updated_at": sample_user.updated_at
            }]
        }
        
        result = await repo.get_by_email(sample_user.email)
        
        assert result.user_id == sample_user.user_id
        assert result.email == sample_user.email
        assert result.first_name == sample_user.first_name
        table.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_repo):
        repo, table, client = user_repo
        table.query.return_value = {"Items": []}
        
        result = await repo.get_by_email("notfound@example.com")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, user_repo, sample_user):
        repo, table, client = user_repo
        table.query.return_value = {
            "Items": [{
                "user_id": sample_user.user_id,
                "first_name": sample_user.first_name,
                "last_name": sample_user.last_name,
                "email": sample_user.email,
                "password": sample_user.password,
                "role": sample_user.role,
                "created_at": sample_user.created_at,
                "updated_at": sample_user.updated_at
            }]
        }
        
        result = await repo.get_by_id(sample_user.user_id)
        
        assert result.user_id == sample_user.user_id
        assert result.email == sample_user.email
        table.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repo):
        repo, table, client = user_repo
        table.query.return_value = {"Items": []}
        
        result = await repo.get_by_id("123e4567-e89b-12d3-a456-426614174000")
        
        assert result is None


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repo, sample_user):
        repo, table, client = user_repo
        client.transact_write_items.return_value = {}
        
        await repo.delete(sample_user.user_id, sample_user.email)
        
        assert client.transact_write_items.call_count == 1
        call_args = client.transact_write_items.call_args[1]
        transact_items = call_args["TransactItems"]
        assert len(transact_items) == 2
        assert transact_items[0]["Delete"]["Key"]["PK"] == f"EMAIL#{sample_user.email}"
        assert transact_items[0]["Delete"]["Key"]["SK"] == f"USER#{sample_user.user_id}"
        assert transact_items[1]["Delete"]["Key"]["PK"] == f"USER#{sample_user.user_id}"
        assert transact_items[1]["Delete"]["Key"]["SK"] == "PROFILE"


class TestGetAllUsers:
    @pytest.mark.asyncio
    async def test_get_all_users(self, user_repo, sample_user):
        repo, table, client = user_repo
        table.scan.return_value = {
            "Items": [{
                "user_id": sample_user.user_id,
                "first_name": sample_user.first_name,
                "last_name": sample_user.last_name,
                "email": sample_user.email,
                "password": sample_user.password,
                "role": sample_user.role,
                "created_at": sample_user.created_at,
                "updated_at": sample_user.updated_at
            }]
        }
        
        result = await repo.get_all()
        
        assert len(result) == 1
        assert result[0].user_id == sample_user.user_id
        table.scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_users_empty(self, user_repo):
        repo, table, client = user_repo
        table.scan.return_value = {"Items": []}
        
        result = await repo.get_all()
        
        assert len(result) == 0

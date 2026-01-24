import uuid
from datetime import datetime, timezone
from app.serverful.utils.password_utils import hash_password
from app.serverful.utils.errors import ApplicationError, ErrorCode
from app.serverful.models.models import User
from app.serverful.models.dto import RegisterUserRequest


class UserService:

    def __init__(self, user_repository) -> None:
        self.user_repo = user_repository

    async def register_user(self, user_request: RegisterUserRequest) -> None:
        existing_user = await self.user_repo.get_by_email(user_request.email)
        
        if existing_user:
            raise ApplicationError(ErrorCode.USER_ALREADY_EXISTS)
        
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user_request.password)
        now = int(datetime.now(timezone.utc).timestamp())
        
        user = User(
            user_id=user_id,
            first_name=user_request.first_name,
            last_name=user_request.last_name,
            email=user_request.email,
            password=hashed_password,
            created_at=now,
            updated_at=now
        )
        
        await self.user_repo.create(user)

    async def register_staff_user(self, staff_request) -> None:
        existing_user = await self.user_repo.get_by_email(staff_request.email)
        
        if existing_user:
            raise ApplicationError(ErrorCode.USER_ALREADY_EXISTS)
        
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(staff_request.password)
        now = int(datetime.now(timezone.utc).timestamp())
        
        user = User(
            user_id=user_id,
            first_name=staff_request.first_name,
            last_name=staff_request.last_name,
            email=staff_request.email,
            password=hashed_password,
            role=staff_request.role,
            created_at=now,
            updated_at=now
        )
        
        await self.user_repo.create(user)

    async def delete_user(self, user_id: str) -> None:
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ApplicationError(ErrorCode.USER_NOT_FOUND)
        
        await self.user_repo.delete(user_id, user.email)

    async def get_all_users(self) -> list:
        users = await self.user_repo.get_all()
        return users

    async def get_user_by_id(self, user_id: str):
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            raise ApplicationError(ErrorCode.USER_NOT_FOUND)
        
        return user

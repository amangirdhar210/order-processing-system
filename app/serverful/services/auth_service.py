import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from app.serverful.utils.password_utils import hash_password, verify_password
from app.serverful.utils.jwt_utils import generate_token
from app.serverful.utils.errors import ApplicationError, ErrorCode
from app.serverful.models.models import User
from app.serverful.models.dto import RegisterUserRequest, LoginUserRequest


class AuthService:

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

    async def login_user(self, login_request: LoginUserRequest) -> Dict[str, Any]:
        user = await self.user_repo.get_by_email(login_request.email)
        
        if not user:
            raise ApplicationError(ErrorCode.INVALID_CREDENTIALS)
        
        if not verify_password(user.password, login_request.password):
            raise ApplicationError(ErrorCode.INVALID_CREDENTIALS)
        
        token = generate_token(user.user_id, user.first_name, "user")
        
        return {
            "token": token,
            "user": {
                "id": user.user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        }
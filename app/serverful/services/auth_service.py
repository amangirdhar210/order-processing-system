from typing import Dict, Any
from app.serverful.utils.password_utils import verify_password
from app.serverful.utils.jwt_utils import generate_token
from app.serverful.utils.errors import ApplicationError, ErrorCode
from app.serverful.models.dto import LoginUserRequest


class AuthService:

    def __init__(self, user_repository) -> None:
        self.user_repo = user_repository

    async def login_user(self, login_request: LoginUserRequest) -> Dict[str, Any]:
        user = await self.user_repo.get_by_email(login_request.email)
        
        if not user:
            raise ApplicationError(ErrorCode.INVALID_CREDENTIALS)
        
        if not verify_password(user.password, login_request.password):
            raise ApplicationError(ErrorCode.INVALID_CREDENTIALS)
        
        token = generate_token(user.user_id, user.first_name, user.role)
        
        return {
            "token": token,
            "user": {
                "id": user.user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.role
            }
        }
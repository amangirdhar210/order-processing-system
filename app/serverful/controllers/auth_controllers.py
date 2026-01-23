from fastapi import APIRouter, status
from app.serverful.models.dto import RegisterUserRequest, GenericResponse, LoginUserRequest, LoginUserResponse
from app.serverful.dependencies.dependencies import AuthServiceInstance

auth_router = APIRouter(prefix="/auth")

@auth_router.post("/register", response_model=GenericResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_request: RegisterUserRequest,
    auth_service: AuthServiceInstance,
) -> GenericResponse:
    """Register a new user account"""
    pass

@auth_router.post("/login", response_model=LoginUserResponse, status_code=status.HTTP_200_OK)
async def login(
    login_request: LoginUserRequest,
    auth_service: AuthServiceInstance,
) -> LoginUserResponse:
    """Authenticate user and return access token"""
    pass
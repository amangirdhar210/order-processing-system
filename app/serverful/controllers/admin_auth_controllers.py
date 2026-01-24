from fastapi import APIRouter, Depends, status
from app.serverful.models.dto import GenericResponse, CreateStaffRequest, UserListDTO, UserDTO
from app.serverful.dependencies.auth import require_admin
from app.serverful.dependencies.dependencies import UserServiceInstance


admin_auth_router = APIRouter(
    prefix="/admin/users",
    dependencies=[Depends(require_admin)]
)


@admin_auth_router.get("", response_model=UserListDTO, status_code=status.HTTP_200_OK)
async def get_all_users(
    user_service: UserServiceInstance,
) -> UserListDTO:
    users = await user_service.get_all_users()
    user_dtos = [
        UserDTO(
            id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]
    return UserListDTO(users=user_dtos, count=len(user_dtos))


@admin_auth_router.post("/staff", response_model=GenericResponse, status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    staff_request: CreateStaffRequest,
    user_service: UserServiceInstance,
) -> GenericResponse:
    await user_service.register_staff_user(staff_request)
    return GenericResponse(message=f"{staff_request.role.capitalize()} user created successfully")


@admin_auth_router.delete("/{user_id}", response_model=GenericResponse, status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: str,
    user_service: UserServiceInstance,
) -> GenericResponse:
    await user_service.delete_user(user_id)
    return GenericResponse(message="User deleted successfully")

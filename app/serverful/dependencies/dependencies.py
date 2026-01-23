from typing import Annotated, Any
from fastapi import Depends, Request
from app.serverful.repositories.user_repository import UserRepository
from app.serverful.repositories.order_repository import OrderRepository
from app.serverful.services.auth_service import AuthService
from app.serverful.services.order_service import OrderService
from app.serverful.services.sns_service import SnsService


def get_dynamodb_resource(request: Request) -> Any:
    return request.app.state.dynamodb_resource


def get_sns_client(request: Request) -> Any:
    return request.app.state.sns_client


def get_user_repository(request: Request) -> UserRepository:
    return request.app.state.user_repo


def get_order_repository(request: Request) -> OrderRepository:
    return request.app.state.order_repo


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_order_service(request: Request) -> OrderService:
    return request.app.state.order_service


def get_sns_service(request: Request) -> SnsService:
    return request.app.state.sns_service


DynamoDBResource = Annotated[Any, Depends(get_dynamodb_resource)]
SNSClientResource = Annotated[Any, Depends(get_sns_client)]
UserRepoInstance = Annotated[UserRepository, Depends(get_user_repository)]
OrderRepoInstance = Annotated[OrderRepository, Depends(get_order_repository)]
AuthServiceInstance = Annotated[AuthService, Depends(get_auth_service)]
OrderServiceInstance = Annotated[OrderService, Depends(get_order_service)]
SNSServiceInstance = Annotated[SnsService, Depends(get_sns_service)]

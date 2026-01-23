from contextlib import asynccontextmanager
from fastapi import FastAPI
import boto3
from app.serverful.config.config import settings
from app.serverful.repositories.user_repository import UserRepository
from app.serverful.repositories.order_repository import OrderRepository
from app.serverful.services.auth_service import AuthService
from app.serverful.services.order_service import OrderService
from app.serverful.services.sns_service import SnsService


@asynccontextmanager
async def lifespan(app: FastAPI):
    dynamodb_resource = boto3.resource(
        "dynamodb",
        region_name=settings.AWS_REGION
    )
    
    sns_client = boto3.client(
        "sns",
        region_name=settings.AWS_REGION
    )
    
    user_repo = UserRepository(
        dynamodb_resource=dynamodb_resource,
        table_name=settings.DYNAMODB_TABLE_NAME
    )
    
    order_repo = OrderRepository(
        dynamodb_resource=dynamodb_resource,
        table_name=settings.DYNAMODB_TABLE_NAME
    )
    
    sns_service = SnsService(sns_client=sns_client)
    
    auth_service = AuthService(user_repository=user_repo)
    
    order_service = OrderService(
        order_repository=order_repo,
        user_repository=user_repo,
        sns_service=sns_service
    )
    
    app.state.dynamodb_resource = dynamodb_resource
    app.state.sns_client = sns_client
    app.state.user_repo = user_repo
    app.state.order_repo = order_repo
    app.state.sns_service = sns_service
    app.state.auth_service = auth_service
    app.state.order_service = order_service
    
    yield

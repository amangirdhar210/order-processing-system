from contextlib import asynccontextmanager
from fastapi import FastAPI
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from app.serverful.config.config import settings
from app.serverful.repositories.user_repository import UserRepository
from app.serverful.repositories.order_repository import OrderRepository
from app.serverful.services.auth_service import AuthService
from app.serverful.services.user_service import UserService
from app.serverful.services.order_service import OrderService
from app.serverful.services.sns_service import SnsService


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        dynamodb_resource = boto3.resource(
            "dynamodb",
            region_name=settings.AWS_REGION
        )
        
        table = dynamodb_resource.Table(settings.DYNAMODB_TABLE_NAME)
        table.load()
        
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"Failed to connect to DynamoDB: {str(e)}")
    
    try:
        sns_client = boto3.client(
            "sns",
            region_name=settings.AWS_REGION
        )
        sns_client.get_topic_attributes(TopicArn=settings.SNS_TOPIC_ARN)
        
    except (ClientError, BotoCoreError) as e:
        raise RuntimeError(f"Failed to connect to SNS: {str(e)}")
    
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
    
    user_service = UserService(user_repository=user_repo)
    
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
    app.state.user_service = user_service
    app.state.order_service = order_service
    
    yield

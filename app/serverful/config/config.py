import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "order_processing_system")
    SNS_TOPIC_ARN: str = os.getenv("SNS_TOPIC_ARN", "")

    BCRYPT_ROUNDS: int = 12

    API_TITLE: str = "Order Processing System"
    API_VERSION: str = "1.0.0"


settings = Settings()
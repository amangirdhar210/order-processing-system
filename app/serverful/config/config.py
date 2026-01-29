import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "order-processing-local")
    SNS_TOPIC_ARN: str = os.getenv("SNS_TOPIC_ARN", "arn:aws:sns:ap-south-1:278273886744:order-events")

settings = Settings()
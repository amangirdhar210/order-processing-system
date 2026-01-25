import json
import os
import boto3
from typing import Dict, Any
from service import EmailService
from models import OrderNotificationMessage
from repository import UserRepository, OrderRepository


dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])
from_email = os.environ['FROM_EMAIL']

user_repository = UserRepository(table)
order_repository = OrderRepository(table)
email_service = EmailService(user_repository, order_repository, ses, from_email)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    batch_item_failures = []
    
    for record in event['Records']:
        try:
            sqs_body = json.loads(record['body'])
            
            if 'Message' in sqs_body:
                sns_message = json.loads(sqs_body['Message'])
            else:
                sns_message = sqs_body
            
            notification = OrderNotificationMessage(**sns_message)
            
            email_service.process_event(notification)
            
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            print(f"Record: {record}")
            batch_item_failures.append({
                "itemIdentifier": record['messageId']
            })
    
    return {
        "batchItemFailures": batch_item_failures
    }
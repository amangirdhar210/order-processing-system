import json
import os
import boto3
from typing import Dict, Any
from service import EmailService
from models import OrderNotificationMessage


dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])
from_email = os.environ['FROM_EMAIL']

email_service = EmailService(table, ses, from_email)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    processed = 0
    failed = 0
    
    for record in event['Records']:
        try:
            sqs_body = json.loads(record['body'])
            
            if 'Message' in sqs_body:
                sns_message = json.loads(sqs_body['Message'])
            else:
                sns_message = sqs_body
            
            notification = OrderNotificationMessage(**sns_message)
            
            email_service.process_event(notification)
            processed += 1
            
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            print(f"Record: {record}")
            failed += 1
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed,
            'failed': failed
        })
    }
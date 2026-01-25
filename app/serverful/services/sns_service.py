import json
import logging
from botocore.exceptions import ClientError
from app.serverful.models.models import NotificationEvent
from app.serverful.config.config import settings

logger = logging.getLogger(__name__)


class SnsService:

    def __init__(self, sns_client) -> None:
        self.sns_client = sns_client
        self.topic_arn = settings.SNS_TOPIC_ARN

    async def publish_event(self, event: NotificationEvent) -> None:
        message = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "order_id": event.order_id,
            "user_id": event.user_id,
            "occurred_at": event.occurred_at
        }
        
        try:
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Message=json.dumps(message),
                Subject=f"Order Event: {event.event_type.value}",
                MessageAttributes={
                    "event_type": {
                        "DataType": "String",
                        "StringValue": event.event_type.value
                    },
                    "order_id": {
                        "DataType": "String",
                        "StringValue": event.order_id
                    }
                }
            )
            logger.info(f"Published SNS event: {event.event_type.value} for order {event.order_id}, MessageId: {response['MessageId']}")
        except ClientError as e:
            logger.error(f"Failed to publish SNS event: {str(e)}")
            raise
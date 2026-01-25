import pytest
from unittest.mock import Mock, patch, AsyncMock
from botocore.exceptions import ClientError
from app.serverful.services.sns_service import SnsService
from app.serverful.models.models import NotificationEvent, NotificationEventType


class TestSnsService:
    @pytest.fixture
    def mock_sns_client(self):
        return Mock()

    @pytest.fixture
    def sns_service(self, mock_sns_client):
        return SnsService(sns_client=mock_sns_client)

    @pytest.fixture
    def sample_event(self):
        return NotificationEvent(
            event_id="event123",
            event_type=NotificationEventType.ORDER_CREATED,
            order_id="order123",
            user_id="user123",
            occurred_at=1737806400
        )

    @pytest.mark.asyncio
    async def test_publish_event_success(self, sns_service, mock_sns_client, sample_event):
        mock_sns_client.publish.return_value = {"MessageId": "msg123"}
        
        await sns_service.publish_event(sample_event)
        
        mock_sns_client.publish.assert_called_once()
        call_args = mock_sns_client.publish.call_args
        assert call_args.kwargs["TopicArn"] == sns_service.topic_arn
        assert "ORDER_CREATED" in call_args.kwargs["Message"]
        assert call_args.kwargs["Subject"] == "Order Event: ORDER_CREATED"

    @pytest.mark.asyncio
    async def test_publish_event_message_attributes(self, sns_service, mock_sns_client, sample_event):
        mock_sns_client.publish.return_value = {"MessageId": "msg123"}
        
        await sns_service.publish_event(sample_event)
        
        call_args = mock_sns_client.publish.call_args
        attributes = call_args.kwargs["MessageAttributes"]
        assert attributes["event_type"]["StringValue"] == "ORDER_CREATED"
        assert attributes["order_id"]["StringValue"] == "order123"

    @pytest.mark.asyncio
    async def test_publish_event_payment_confirmed(self, sns_service, mock_sns_client):
        event = NotificationEvent(
            event_id="event456",
            event_type=NotificationEventType.PAYMENT_CONFIRMED,
            order_id="order456",
            user_id="user456",
            occurred_at=1737810000
        )
        mock_sns_client.publish.return_value = {"MessageId": "msg456"}
        
        await sns_service.publish_event(event)
        
        call_args = mock_sns_client.publish.call_args
        assert "PAYMENT_CONFIRMED" in call_args.kwargs["Message"]
        assert call_args.kwargs["Subject"] == "Order Event: PAYMENT_CONFIRMED"

    @pytest.mark.asyncio
    async def test_publish_event_client_error(self, sns_service, mock_sns_client, sample_event):
        mock_sns_client.publish.side_effect = ClientError(
            {"Error": {"Code": "NotFound", "Message": "Topic not found"}},
            "publish"
        )
        
        with pytest.raises(ClientError):
            await sns_service.publish_event(sample_event)

    @pytest.mark.asyncio
    async def test_publish_event_all_event_types(self, sns_service, mock_sns_client):
        event_types = [
            NotificationEventType.ORDER_CREATED,
            NotificationEventType.PAYMENT_CONFIRMED,
            NotificationEventType.FULFILLMENT_STARTED,
            NotificationEventType.FULFILLED,
            NotificationEventType.PAYMENT_FAILED,
            NotificationEventType.FULFILLMENT_CANCELLED,
            NotificationEventType.ORDER_CANCELLED,
        ]
        
        for event_type in event_types:
            event = NotificationEvent(
                event_id=f"event_{event_type.value}",
                event_type=event_type,
                order_id="order123",
                user_id="user123",
                occurred_at=1737806400
            )
            mock_sns_client.publish.return_value = {"MessageId": "msg123"}
            
            await sns_service.publish_event(event)
            
            call_args = mock_sns_client.publish.call_args
            assert event_type.value in call_args.kwargs["Message"]

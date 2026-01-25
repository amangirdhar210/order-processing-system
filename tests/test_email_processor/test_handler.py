import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

os.environ['DYNAMODB_TABLE_NAME'] = 'test-table'
os.environ['FROM_EMAIL'] = 'test@example.com'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app/serverless/email-processor'))


class TestLambdaHandler:
    @pytest.fixture
    def sample_sns_sqs_event(self):
        return {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'Message': json.dumps({
                            'event_id': 'event-123',
                            'event_type': 'ORDER_CREATED',
                            'order_id': 'order-123',
                            'user_id': 'user-123',
                            'occurred_at': 1234567890
                        })
                    })
                }
            ]
        }
    
    @pytest.fixture
    def sample_direct_sqs_event(self):
        return {
            'Records': [
                {
                    'messageId': 'msg-2',
                    'body': json.dumps({
                        'event_id': 'event-456',
                        'event_type': 'PAYMENT_CONFIRMED',
                        'order_id': 'order-456',
                        'user_id': 'user-456',
                        'occurred_at': 1234567890
                    })
                }
            ]
        }
    
    @pytest.fixture
    def sample_multiple_records_event(self):
        return {
            'Records': [
                {
                    'messageId': 'msg-1',
                    'body': json.dumps({
                        'Message': json.dumps({
                            'event_id': 'event-123',
                            'event_type': 'ORDER_CREATED',
                            'order_id': 'order-123',
                            'user_id': 'user-123',
                            'occurred_at': 1234567890
                        })
                    })
                },
                {
                    'messageId': 'msg-2',
                    'body': json.dumps({
                        'Message': json.dumps({
                            'event_id': 'event-456',
                            'event_type': 'PAYMENT_CONFIRMED',
                            'order_id': 'order-456',
                            'user_id': 'user-456',
                            'occurred_at': 1234567890
                        })
                    })
                }
            ]
        }
    
    @pytest.fixture
    def mock_email_service(self):
        with patch('handler.email_service') as mock:
            yield mock
    
    def test_lambda_handler_sns_sqs_message_success(self, sample_sns_sqs_event, mock_email_service):
        from handler import lambda_handler
        
        result = lambda_handler(sample_sns_sqs_event, None)
        
        assert result == {'batchItemFailures': []}
        mock_email_service.process_event.assert_called_once()
        
        call_args = mock_email_service.process_event.call_args[0][0]
        assert call_args.event_id == 'event-123'
        assert call_args.event_type == 'ORDER_CREATED'
        assert call_args.order_id == 'order-123'
        assert call_args.user_id == 'user-123'
    
    def test_lambda_handler_direct_sqs_message_success(self, sample_direct_sqs_event, mock_email_service):
        from handler import lambda_handler
        
        result = lambda_handler(sample_direct_sqs_event, None)
        
        assert result == {'batchItemFailures': []}
        mock_email_service.process_event.assert_called_once()
        
        call_args = mock_email_service.process_event.call_args[0][0]
        assert call_args.event_id == 'event-456'
        assert call_args.event_type == 'PAYMENT_CONFIRMED'
    
    def test_lambda_handler_multiple_records_success(self, sample_multiple_records_event, mock_email_service):
        from handler import lambda_handler
        
        result = lambda_handler(sample_multiple_records_event, None)
        
        assert result == {'batchItemFailures': []}
        assert mock_email_service.process_event.call_count == 2
    
    def test_lambda_handler_processing_error(self, sample_sns_sqs_event, mock_email_service):
        from handler import lambda_handler
        
        mock_email_service.process_event.side_effect = Exception("Processing error")
        
        result = lambda_handler(sample_sns_sqs_event, None)
        
        assert len(result['batchItemFailures']) == 1
        assert result['batchItemFailures'][0]['itemIdentifier'] == 'msg-1'
    
    def test_lambda_handler_partial_failure(self, sample_multiple_records_event, mock_email_service):
        from handler import lambda_handler
        
        mock_email_service.process_event.side_effect = [None, Exception("Second record failed")]
        
        result = lambda_handler(sample_multiple_records_event, None)
        
        assert len(result['batchItemFailures']) == 1
        assert result['batchItemFailures'][0]['itemIdentifier'] == 'msg-2'
    
    def test_lambda_handler_invalid_json(self, mock_email_service):
        from handler import lambda_handler
        
        event = {
            'Records': [
                {
                    'messageId': 'msg-bad',
                    'body': 'invalid json'
                }
            ]
        }
        
        result = lambda_handler(event, None)
        
        assert len(result['batchItemFailures']) == 1
        assert result['batchItemFailures'][0]['itemIdentifier'] == 'msg-bad'
        mock_email_service.process_event.assert_not_called()
    
    def test_lambda_handler_invalid_notification_data(self, mock_email_service):
        from handler import lambda_handler
        
        event = {
            'Records': [
                {
                    'messageId': 'msg-invalid',
                    'body': json.dumps({
                        'Message': json.dumps({
                            'event_id': 'event-123',
                            'event_type': 'ORDER_CREATED'
                        })
                    })
                }
            ]
        }
        
        result = lambda_handler(event, None)
        
        assert len(result['batchItemFailures']) == 1
        assert result['batchItemFailures'][0]['itemIdentifier'] == 'msg-invalid'
    
    def test_lambda_handler_empty_records(self, mock_email_service):
        from handler import lambda_handler
        
        event = {'Records': []}
        
        result = lambda_handler(event, None)
        
        assert result == {'batchItemFailures': []}
        mock_email_service.process_event.assert_not_called()
    
    def test_lambda_handler_all_records_fail(self, sample_multiple_records_event, mock_email_service):
        from handler import lambda_handler
        
        mock_email_service.process_event.side_effect = Exception("All failed")
        
        result = lambda_handler(sample_multiple_records_event, None)
        
        assert len(result['batchItemFailures']) == 2
        assert result['batchItemFailures'][0]['itemIdentifier'] == 'msg-1'
        assert result['batchItemFailures'][1]['itemIdentifier'] == 'msg-2'

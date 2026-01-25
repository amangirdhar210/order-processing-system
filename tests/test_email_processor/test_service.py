import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app/serverless/email-processor'))

from service import EmailService
from models import OrderNotificationMessage


class TestEmailService:
    @pytest.fixture
    def mock_user_repo(self):
        return Mock()
    
    @pytest.fixture
    def mock_order_repo(self):
        return Mock()
    
    @pytest.fixture
    def mock_ses_client(self):
        return Mock()
    
    @pytest.fixture
    def email_service(self, mock_user_repo, mock_order_repo, mock_ses_client):
        return EmailService(mock_user_repo, mock_order_repo, mock_ses_client, 'noreply@example.com')
    
    @pytest.fixture
    def sample_user(self):
        return {
            'user_id': 'user-123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com'
        }
    
    @pytest.fixture
    def sample_order(self):
        return {
            'order_id': 'order-123',
            'user_id': 'user-123',
            'order_status': 'PAYMENT_PENDING',
            'delivery_address': '123 Main St',
            'total_amount': '100.00',
            'items': [
                {
                    'product_id': 'prod-1',
                    'product_name': 'Product A',
                    'quantity': 2,
                    'unit_price': '25.00',
                    'subtotal': '50.00'
                },
                {
                    'product_id': 'prod-2',
                    'product_name': 'Product B',
                    'quantity': 1,
                    'unit_price': '50.00',
                    'subtotal': '50.00'
                }
            ]
        }
    
    @pytest.fixture
    def sample_notification(self):
        return OrderNotificationMessage(
            event_id='event-123',
            event_type='ORDER_CREATED',
            order_id='order-123',
            user_id='user-123',
            occurred_at=1234567890
        )
    
    def test_process_event_order_created(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_user, sample_order, sample_notification):
        mock_user_repo.get_user.return_value = sample_user
        mock_order_repo.get_order.return_value = sample_order
        
        email_service.process_event(sample_notification)
        
        mock_user_repo.get_user.assert_called_once_with('user-123')
        mock_order_repo.get_order.assert_called_once_with('order-123')
        mock_ses_client.send_email.assert_called_once()
        
        call_args = mock_ses_client.send_email.call_args[1]
        assert call_args['Source'] == 'noreply@example.com'
        assert call_args['Destination']['ToAddresses'] == ['john@example.com']
        assert 'Order Confirmation' in call_args['Message']['Subject']['Data']
    
    def test_process_event_user_not_found(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_notification):
        mock_user_repo.get_user.return_value = None
        
        email_service.process_event(sample_notification)
        
        mock_user_repo.get_user.assert_called_once_with('user-123')
        mock_order_repo.get_order.assert_not_called()
        mock_ses_client.send_email.assert_not_called()
    
    def test_process_event_order_not_found(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_user, sample_notification):
        mock_user_repo.get_user.return_value = sample_user
        mock_order_repo.get_order.return_value = None
        
        email_service.process_event(sample_notification)
        
        mock_user_repo.get_user.assert_called_once_with('user-123')
        mock_order_repo.get_order.assert_called_once_with('order-123')
        mock_ses_client.send_email.assert_not_called()
    
    def test_process_event_unknown_event_type(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_user, sample_order):
        mock_user_repo.get_user.return_value = sample_user
        mock_order_repo.get_order.return_value = sample_order
        
        notification = OrderNotificationMessage(
            event_id='event-123',
            event_type='UNKNOWN_EVENT',
            order_id='order-123',
            user_id='user-123',
            occurred_at=1234567890
        )
        
        email_service.process_event(notification)
        
        mock_ses_client.send_email.assert_not_called()
    
    def test_process_event_payment_confirmed(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_user, sample_order):
        mock_user_repo.get_user.return_value = sample_user
        sample_order['payment_details'] = {
            'payment_method': 'credit_card',
            'transaction_id': 'txn-123',
            'payment_status': 'success'
        }
        mock_order_repo.get_order.return_value = sample_order
        
        notification = OrderNotificationMessage(
            event_id='event-123',
            event_type='PAYMENT_CONFIRMED',
            order_id='order-123',
            user_id='user-123',
            occurred_at=1234567890
        )
        
        email_service.process_event(notification)
        
        mock_ses_client.send_email.assert_called_once()
        call_args = mock_ses_client.send_email.call_args[1]
        assert 'Payment Confirmed' in call_args['Message']['Subject']['Data']
    
    def test_process_event_fulfillment_started(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_user, sample_order):
        mock_user_repo.get_user.return_value = sample_user
        mock_order_repo.get_order.return_value = sample_order
        
        notification = OrderNotificationMessage(
            event_id='event-123',
            event_type='FULFILLMENT_STARTED',
            order_id='order-123',
            user_id='user-123',
            occurred_at=1234567890
        )
        
        email_service.process_event(notification)
        
        mock_ses_client.send_email.assert_called_once()
        call_args = mock_ses_client.send_email.call_args[1]
        assert 'Order Fulfillment Started' in call_args['Message']['Subject']['Data']
    
    def test_process_event_fulfilled(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_user, sample_order):
        mock_user_repo.get_user.return_value = sample_user
        mock_order_repo.get_order.return_value = sample_order
        
        notification = OrderNotificationMessage(
            event_id='event-123',
            event_type='FULFILLED',
            order_id='order-123',
            user_id='user-123',
            occurred_at=1234567890
        )
        
        email_service.process_event(notification)
        
        mock_ses_client.send_email.assert_called_once()
        call_args = mock_ses_client.send_email.call_args[1]
        assert 'Order Fulfilled' in call_args['Message']['Subject']['Data']
    
    def test_process_event_payment_failed(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_user, sample_order):
        mock_user_repo.get_user.return_value = sample_user
        mock_order_repo.get_order.return_value = sample_order
        
        notification = OrderNotificationMessage(
            event_id='event-123',
            event_type='PAYMENT_FAILED',
            order_id='order-123',
            user_id='user-123',
            occurred_at=1234567890
        )
        
        email_service.process_event(notification)
        
        mock_ses_client.send_email.assert_called_once()
        call_args = mock_ses_client.send_email.call_args[1]
        assert 'Payment Failed' in call_args['Message']['Subject']['Data']
    
    def test_process_event_fulfillment_canceled(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_user, sample_order):
        mock_user_repo.get_user.return_value = sample_user
        mock_order_repo.get_order.return_value = sample_order
        
        notification = OrderNotificationMessage(
            event_id='event-123',
            event_type='FULFILLMENT_CANCELED',
            order_id='order-123',
            user_id='user-123',
            occurred_at=1234567890
        )
        
        email_service.process_event(notification)
        
        mock_ses_client.send_email.assert_called_once()
        call_args = mock_ses_client.send_email.call_args[1]
        assert 'Order Fulfillment Cancelled' in call_args['Message']['Subject']['Data']
    
    def test_process_event_order_cancelled(self, email_service, mock_user_repo, mock_order_repo, mock_ses_client, sample_user, sample_order):
        mock_user_repo.get_user.return_value = sample_user
        mock_order_repo.get_order.return_value = sample_order
        
        notification = OrderNotificationMessage(
            event_id='event-123',
            event_type='ORDER_CANCELLED',
            order_id='order-123',
            user_id='user-123',
            occurred_at=1234567890
        )
        
        email_service.process_event(notification)
        
        mock_ses_client.send_email.assert_called_once()
        call_args = mock_ses_client.send_email.call_args[1]
        assert 'Order Cancelled' in call_args['Message']['Subject']['Data']
    
    def test_send_email_success(self, email_service, mock_ses_client):
        email_service._send_email('test@example.com', 'Test Subject', '<html>Test Body</html>')
        
        mock_ses_client.send_email.assert_called_once_with(
            Source='noreply@example.com',
            Destination={'ToAddresses': ['test@example.com']},
            Message={
                'Subject': {'Data': 'Test Subject', 'Charset': 'UTF-8'},
                'Body': {'Html': {'Data': '<html>Test Body</html>', 'Charset': 'UTF-8'}}
            }
        )
    
    def test_send_email_failure(self, email_service, mock_ses_client):
        mock_ses_client.send_email.side_effect = Exception("SES error")
        
        with pytest.raises(Exception, match="SES error"):
            email_service._send_email('test@example.com', 'Test Subject', '<html>Test Body</html>')
    
    def test_format_order_items(self, email_service, sample_order):
        result = email_service._format_order_items(sample_order)
        
        assert 'Product A' in result
        assert 'Product B' in result
        assert '2' in result
        assert '25.00' in result
        assert '50.00' in result
        assert '100.00' in result

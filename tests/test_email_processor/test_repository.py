import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../app/serverless/email-processor'))

from repository import UserRepository, OrderRepository


class TestUserRepository:
    @pytest.fixture
    def mock_table(self):
        return Mock()
    
    @pytest.fixture
    def user_repository(self, mock_table):
        return UserRepository(mock_table)
    
    def test_get_user_success(self, user_repository, mock_table):
        user_data = {
            'user_id': 'user-123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com'
        }
        mock_table.query.return_value = {'Items': [user_data]}
        
        result = user_repository.get_user('user-123')
        
        assert result == user_data
        mock_table.query.assert_called_once_with(
            KeyConditionExpression='PK = :pk AND SK = :sk',
            ExpressionAttributeValues={
                ':pk': 'USER#user-123',
                ':sk': 'PROFILE'
            }
        )
    
    def test_get_user_not_found(self, user_repository, mock_table):
        mock_table.query.return_value = {'Items': []}
        
        result = user_repository.get_user('user-999')
        
        assert result is None
    
    def test_get_user_exception(self, user_repository, mock_table):
        mock_table.query.side_effect = Exception("DynamoDB error")
        
        result = user_repository.get_user('user-123')
        
        assert result is None


class TestOrderRepository:
    @pytest.fixture
    def mock_table(self):
        return Mock()
    
    @pytest.fixture
    def order_repository(self, mock_table):
        return OrderRepository(mock_table)
    
    def test_get_order_success(self, order_repository, mock_table):
        order_data = {
            'order_id': 'order-123',
            'user_id': 'user-123',
            'items': [{'product_name': 'Product A', 'quantity': 2}],
            'total_amount': '100.00'
        }
        mock_table.query.return_value = {'Items': [order_data]}
        
        result = order_repository.get_order('order-123')
        
        assert result == order_data
        mock_table.query.assert_called_once_with(
            KeyConditionExpression='PK = :pk AND SK = :sk',
            ExpressionAttributeValues={
                ':pk': 'ORDER#order-123',
                ':sk': 'DETAILS'
            }
        )
    
    def test_get_order_not_found(self, order_repository, mock_table):
        mock_table.query.return_value = {'Items': []}
        
        result = order_repository.get_order('order-999')
        
        assert result is None
    
    def test_get_order_exception(self, order_repository, mock_table):
        mock_table.query.side_effect = Exception("DynamoDB error")
        
        result = order_repository.get_order('order-123')
        
        assert result is None

from typing import Dict, Any, Optional


class UserRepository:
    def __init__(self, table):
        self.table = table

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id from DynamoDB"""
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND SK = :sk',
                ExpressionAttributeValues={
                    ':pk': f'USER#{user_id}',
                    ':sk': 'PROFILE'
                }
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            print(f"Error fetching user {user_id}: {str(e)}")
            return None


class OrderRepository:
    def __init__(self, table):
        self.table = table

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by order_id from DynamoDB"""
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND SK = :sk',
                ExpressionAttributeValues={
                    ':pk': f'ORDER#{order_id}',
                    ':sk': 'DETAILS'
                }
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            print(f"Error fetching order {order_id}: {str(e)}")
            return None

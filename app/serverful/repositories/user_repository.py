import asyncio
from boto3.dynamodb.types import TypeSerializer


class UserRepository:
    def __init__(self, dynamodb_resource, table_name):
        self.dynamodb_resource = dynamodb_resource
        self.table = dynamodb_resource.Table(table_name)
        self.client = dynamodb_resource.meta.client
        self.serializer = TypeSerializer()

    async def create(self, user):
        item_by_email = {
            "PK": f"EMAIL#{user.email}",
            "SK": f"USER#{user.user_id}",
            "user_id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "password": user.password,
            "role": user.role,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        
        item_by_id = {
            "PK": f"USER#{user.user_id}",
            "SK": "PROFILE",
            "user_id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "password": user.password,
            "role": user.role,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        
        transact_items = [
            {
                "Put": {
                    "TableName": self.table.table_name,
                    "Item": {k: self.serializer.serialize(v) for k, v in item_by_email.items()}
                }
            },
            {
                "Put": {
                    "TableName": self.table.table_name,
                    "Item": {k: self.serializer.serialize(v) for k, v in item_by_id.items()}
                }
            }
        ]
        
        await asyncio.to_thread(self.client.transact_write_items, TransactItems=transact_items)

    async def get_by_email(self, email):
        response = await asyncio.to_thread(
            self.table.query,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={
                ":pk": f"EMAIL#{email}"
            }
        )
        
        items = response.get("Items", [])
        
        if not items:
            return None
        
        return self._unmarshal_user(items[0])

    async def get_by_id(self, user_id):
        response = await asyncio.to_thread(
            self.table.query,
            KeyConditionExpression="PK = :pk AND SK = :sk",
            ExpressionAttributeValues={
                ":pk": f"USER#{user_id}",
                ":sk": "PROFILE"
            }
        )
        
        items = response.get("Items", [])
        
        if not items:
            return None
        
        return self._unmarshal_user(items[0])

    async def delete(self, user_id, email):
        key_by_email = {
            "PK": f"EMAIL#{email}",
            "SK": f"USER#{user_id}"
        }
        
        key_by_id = {
            "PK": f"USER#{user_id}",
            "SK": "PROFILE"
        }
        
        transact_items = [
            {
                "Delete": {
                    "TableName": self.table.table_name,
                    "Key": {k: self.serializer.serialize(v) for k, v in key_by_email.items()}
                }
            },
            {
                "Delete": {
                    "TableName": self.table.table_name,
                    "Key": {k: self.serializer.serialize(v) for k, v in key_by_id.items()}
                }
            }
        ]
        
        await asyncio.to_thread(self.client.transact_write_items, TransactItems=transact_items)

    def _unmarshal_user(self, item):
        from app.serverful.models.models import User
        
        return User(
            user_id=item.get("user_id"),
            first_name=item.get("first_name"),
            last_name=item.get("last_name"),
            email=item.get("email"),
            password=item.get("password"),
            role=item.get("role", "user"),
            created_at=item.get("created_at", 0),
            updated_at=item.get("updated_at", 0)
        ) 


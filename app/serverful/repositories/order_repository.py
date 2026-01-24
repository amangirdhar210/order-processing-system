from typing import List, Optional
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from boto3.dynamodb.types import TypeSerializer
from app.serverful.models.models import Order, OrderItem, PaymentDetails, StatusChange, OrderStatus


class OrderRepository:

    def __init__(self, dynamodb_resource, table_name):
        self.dynamodb_resource = dynamodb_resource
        self.table = dynamodb_resource.Table(table_name)
        self.client = dynamodb_resource.meta.client
        self.serializer = TypeSerializer()

    async def create(self, order: Order) -> None:
        date_prefix = datetime.fromtimestamp(order.created_at, timezone.utc).strftime("%Y-%m-%d")
        
        base_item = {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "delivery_address": order.delivery_address,
            "status": order.status.value,
            "items": [{
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal)
            } for item in order.items],
            "total_amount": str(order.total_amount),
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "status_history": []
        }
        
        if order.payment_details:
            base_item["payment_details"] = {
                "payment_method": order.payment_details.payment_method,
                "transaction_id": order.payment_details.transaction_id,
                "payment_status": order.payment_details.payment_status,
                "processed_at": order.payment_details.processed_at
            }
        
        item_by_status = {"PK": f"STATUS#{order.status.value}", "SK": f"{date_prefix}#ORDER#{order.order_id}", **base_item}
        item_by_user = {"PK": f"ORDERS#{order.user_id}", "SK": f"ORDER#{order.order_id}", **base_item}
        item_by_order_id = {"PK": f"ORDER#{order.order_id}", "SK": "DETAILS", **base_item}
        
        transact_items = [
            {"Put": {"TableName": self.table.table_name, "Item": {k: self.serializer.serialize(v) for k, v in item_by_status.items()}}},
            {"Put": {"TableName": self.table.table_name, "Item": {k: self.serializer.serialize(v) for k, v in item_by_user.items()}}},
            {"Put": {"TableName": self.table.table_name, "Item": {k: self.serializer.serialize(v) for k, v in item_by_order_id.items()}}}
        ]
        
        await asyncio.to_thread(self.client.transact_write_items, TransactItems=transact_items)

    async def get_by_user_and_order(self, user_id: str, order_id: str) -> Optional[Order]:
        response = await asyncio.to_thread(
            self.table.query,
            KeyConditionExpression="PK = :pk AND SK = :sk",
            ExpressionAttributeValues={
                ":pk": f"ORDERS#{user_id}",
                ":sk": f"ORDER#{order_id}"
            }
        )
        
        items = response.get("Items", [])
        return self._unmarshal_order(items[0]) if items else None

    async def get_by_order_id(self, order_id: str) -> Optional[Order]:
        response = await asyncio.to_thread(
            self.table.query,
            KeyConditionExpression="PK = :pk AND SK = :sk",
            ExpressionAttributeValues={
                ":pk": f"ORDER#{order_id}",
                ":sk": "DETAILS"
            }
        )
        
        items = response.get("Items", [])
        return self._unmarshal_order(items[0]) if items else None

    async def get_by_user(self, user_id: str) -> List[Order]:
        response = await asyncio.to_thread(
            self.table.query,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={
                ":pk": f"ORDERS#{user_id}"
            }
        )
        
        items = response.get("Items", [])
        return [self._unmarshal_order(item) for item in items]

    async def get_by_status(self, status: OrderStatus) -> List[Order]:
        response = await asyncio.to_thread(
            self.table.query,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={
                ":pk": f"STATUS#{status.value}"
            },
            ScanIndexForward=False
        )
        
        items = response.get("Items", [])
        return [self._unmarshal_order(item) for item in items]

    async def get_all(self) -> List[Order]:
        all_orders = []
        for status in OrderStatus:
            orders = await self.get_by_status(status)
            all_orders.extend(orders)
        return all_orders

    async def update_status(self, order: Order, old_status: OrderStatus) -> None:
        date_prefix = datetime.fromtimestamp(order.created_at, timezone.utc).strftime("%Y-%m-%d")
        
        new_item_by_status = {
            "PK": f"STATUS#{order.status.value}",
            "SK": f"{date_prefix}#ORDER#{order.order_id}",
            "order_id": order.order_id,
            "user_id": order.user_id,
            "delivery_address": order.delivery_address,
            "status": order.status.value,
            "items": [{
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal)
            } for item in order.items],
            "total_amount": str(order.total_amount),
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "status_history": [{
                "from_status": sc.from_status.value,
                "to_status": sc.to_status.value,
                "changed_at": sc.changed_at,
                "changed_by": sc.changed_by
            } for sc in order.status_history]
        }
        
        if order.payment_details:
            new_item_by_status["payment_details"] = {
                "payment_method": order.payment_details.payment_method,
                "transaction_id": order.payment_details.transaction_id,
                "payment_status": order.payment_details.payment_status,
                "processed_at": order.payment_details.processed_at
            }
        
        update_expression_parts = [
            "status = :status",
            "updated_at = :updated_at",
            "status_history = :status_history"
        ]
        expression_values = {
            ":status": order.status.value,
            ":updated_at": order.updated_at,
            ":status_history": [{
                "from_status": sc.from_status.value,
                "to_status": sc.to_status.value,
                "changed_at": sc.changed_at,
                "changed_by": sc.changed_by
            } for sc in order.status_history]
        }
        
        if order.payment_details:
            update_expression_parts.append("payment_details = :payment_details")
            expression_values[":payment_details"] = {
                "payment_method": order.payment_details.payment_method,
                "transaction_id": order.payment_details.transaction_id,
                "payment_status": order.payment_details.payment_status,
                "processed_at": order.payment_details.processed_at
            }
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        transact_items = [
            {"Delete": {"TableName": self.table.table_name, "Key": {k: self.serializer.serialize(v) for k, v in {"PK": f"STATUS#{old_status.value}", "SK": f"{date_prefix}#ORDER#{order.order_id}"}.items()}}},
            {"Put": {"TableName": self.table.table_name, "Item": {k: self.serializer.serialize(v) for k, v in new_item_by_status.items()}}},
            {"Update": {
                "TableName": self.table.table_name,
                "Key": {k: self.serializer.serialize(v) for k, v in {"PK": f"ORDERS#{order.user_id}", "SK": f"ORDER#{order.order_id}"}.items()},
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": {k: self.serializer.serialize(v) for k, v in expression_values.items()}
            }},
            {"Update": {
                "TableName": self.table.table_name,
                "Key": {k: self.serializer.serialize(v) for k, v in {"PK": f"ORDER#{order.order_id}", "SK": "DETAILS"}.items()},
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": {k: self.serializer.serialize(v) for k, v in expression_values.items()}
            }}
        ]
        
        await asyncio.to_thread(self.client.transact_write_items, TransactItems=transact_items)

    async def delete(self, user_id: str, order_id: str, status: OrderStatus) -> None:
        order = await self.get_by_order_id(order_id)
        if not order:
            return
        
        date_prefix = datetime.fromtimestamp(order.created_at, timezone.utc).strftime("%Y-%m-%d")
        
        keys = [
            {"PK": f"STATUS#{status.value}", "SK": f"{date_prefix}#ORDER#{order_id}"},
            {"PK": f"ORDERS#{user_id}", "SK": f"ORDER#{order_id}"},
            {"PK": f"ORDER#{order_id}", "SK": "DETAILS"}
        ]
        
        transact_items = [
            {"Delete": {"TableName": self.table.table_name, "Key": {k: self.serializer.serialize(v) for k, v in key.items()}}}
            for key in keys
        ]
        
        await asyncio.to_thread(self.client.transact_write_items, TransactItems=transact_items)

    def _unmarshal_order(self, item: dict) -> Order:
        items = [OrderItem(
            product_id=i["product_id"],
            product_name=i["product_name"],
            quantity=i["quantity"],
            unit_price=Decimal(i["unit_price"]),
            subtotal=Decimal(i["subtotal"])
        ) for i in item.get("items", [])]
        
        payment_details = None
        if "payment_details" in item and item["payment_details"]:
            pd = item["payment_details"]
            payment_details = PaymentDetails(
                payment_method=pd["payment_method"],
                transaction_id=pd["transaction_id"],
                payment_status=pd["payment_status"],
                processed_at=pd.get("processed_at")
            )
        
        status_history = [StatusChange(
            from_status=OrderStatus(sc["from_status"]),
            to_status=OrderStatus(sc["to_status"]),
            changed_at=sc["changed_at"],
            changed_by=sc["changed_by"]
        ) for sc in item.get("status_history", [])]
        
        return Order(
            order_id=item["order_id"],
            user_id=item["user_id"],
            delivery_address=item["delivery_address"],
            status=OrderStatus(item["status"]),
            items=items,
            total_amount=Decimal(item["total_amount"]),
            payment_details=payment_details,
            status_history=status_history,
            created_at=item["created_at"],
            updated_at=item["updated_at"]
        )
import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import datetime, timezone
from app.serverful.repositories.order_repository import OrderRepository
from app.serverful.models.models import Order, OrderStatus, OrderItem, PaymentDetails, StatusChange


@pytest.fixture
def mock_dynamodb():
    dynamodb = MagicMock()
    table = MagicMock()
    table.table_name = "test-table"
    client = MagicMock()
    dynamodb.Table.return_value = table
    dynamodb.meta.client = client
    return dynamodb, table, client


@pytest.fixture
def order_repo(mock_dynamodb):
    dynamodb, table, client = mock_dynamodb
    return OrderRepository(dynamodb, "test-table"), table, client


@pytest.fixture
def sample_order():
    return Order(
        order_id="order-123",
        user_id="123e4567-e89b-12d3-a456-426614174000",
        delivery_address="123 Main St",
        status=OrderStatus.PAYMENT_PENDING,
        items=[OrderItem(
            product_id="prod-1",
            product_name="Product 1",
            quantity=2,
            unit_price=Decimal("10.00"),
            subtotal=Decimal("20.00")
        )],
        total_amount=Decimal("20.00"),
        created_at=1234567890,
        updated_at=1234567890
    )


@pytest.fixture
def sample_order_dict():
    return {
        "order_id": "order-123",
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "delivery_address": "123 Main St",
        "order_status": "PAYMENT_PENDING",
        "items": [{
            "product_id": "prod-1",
            "product_name": "Product 1",
            "quantity": 2,
            "unit_price": "10.00",
            "subtotal": "20.00"
        }],
        "total_amount": "20.00",
        "created_at": 1234567890,
        "updated_at": 1234567890,
        "status_history": []
    }


class TestCreateOrder:
    @pytest.mark.asyncio
    async def test_create_order_success(self, order_repo, sample_order):
        repo, table, client = order_repo
        client.transact_write_items.return_value = {}
        
        await repo.create(sample_order)
        
        assert client.transact_write_items.call_count == 1
        call_args = client.transact_write_items.call_args[1]
        transact_items = call_args["TransactItems"]
        assert len(transact_items) == 3
        assert transact_items[0]["Put"]["Item"]["PK"].startswith("STATUS#PAYMENT_PENDING")
        assert transact_items[1]["Put"]["Item"]["PK"] == f"ORDERS#{sample_order.user_id}"
        assert transact_items[2]["Put"]["Item"]["PK"] == f"ORDER#{sample_order.order_id}"

    @pytest.mark.asyncio
    async def test_create_order_with_payment_details(self, order_repo, sample_order):
        repo, table, client = order_repo
        client.transact_write_items.return_value = {}
        sample_order.payment_details = PaymentDetails(
            payment_method="credit_card",
            transaction_id="txn-123",
            payment_status="success",
            processed_at=1234567890
        )
        
        await repo.create(sample_order)
        
        call_args = client.transact_write_items.call_args[1]
        transact_items = call_args["TransactItems"]
        assert "payment_details" in transact_items[0]["Put"]["Item"]


class TestGetOrder:
    @pytest.mark.asyncio
    async def test_get_by_user_and_order_success(self, order_repo, sample_order_dict):
        repo, table, client = order_repo
        table.query.return_value = {"Items": [sample_order_dict]}
        
        result = await repo.get_by_user_and_order("123e4567-e89b-12d3-a456-426614174000", "order-123")
        
        assert result.order_id == "order-123"
        assert result.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert result.status == OrderStatus.PAYMENT_PENDING
        table.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_user_and_order_not_found(self, order_repo):
        repo, table, client = order_repo
        table.query.return_value = {"Items": []}
        
        result = await repo.get_by_user_and_order("123e4567-e89b-12d3-a456-426614174000", "order-123")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_order_id_success(self, order_repo, sample_order_dict):
        repo, table, client = order_repo
        table.query.return_value = {"Items": [sample_order_dict]}
        
        result = await repo.get_by_order_id("order-123")
        
        assert result.order_id == "order-123"
        table.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_order_id_not_found(self, order_repo):
        repo, table, client = order_repo
        table.query.return_value = {"Items": []}
        
        result = await repo.get_by_order_id("order-123")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_user(self, order_repo, sample_order_dict):
        repo, table, client = order_repo
        table.query.return_value = {"Items": [sample_order_dict]}
        
        result = await repo.get_by_user("123e4567-e89b-12d3-a456-426614174000")
        
        assert len(result) == 1
        assert result[0].order_id == "order-123"
        table.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_status(self, order_repo, sample_order_dict):
        repo, table, client = order_repo
        table.query.return_value = {"Items": [sample_order_dict]}
        
        result = await repo.get_by_status(OrderStatus.PAYMENT_PENDING)
        
        assert len(result) == 1
        assert result[0].status == OrderStatus.PAYMENT_PENDING
        table.query.assert_called_once()


class TestUpdateOrderStatus:
    @pytest.mark.asyncio
    async def test_update_status_without_payment(self, order_repo, sample_order):
        repo, table, client = order_repo
        client.transact_write_items.return_value = {}
        sample_order.status = OrderStatus.PAYMENT_CONFIRMED
        sample_order.status_history.append(StatusChange(
            from_status=OrderStatus.PAYMENT_PENDING,
            to_status=OrderStatus.PAYMENT_CONFIRMED,
            changed_at=1234567890,
            changed_by="user"
        ))
        
        await repo.update_status(sample_order, OrderStatus.PAYMENT_PENDING)
        
        assert client.transact_write_items.call_count == 1
        call_args = client.transact_write_items.call_args[1]
        transact_items = call_args["TransactItems"]
        assert len(transact_items) == 4
        assert transact_items[0]["Delete"]["Key"]["PK"].startswith("STATUS#PAYMENT_PENDING")
        assert transact_items[1]["Put"]["Item"]["PK"].startswith("STATUS#PAYMENT_CONFIRMED")

    @pytest.mark.asyncio
    async def test_update_status_with_payment(self, order_repo, sample_order):
        repo, table, client = order_repo
        client.transact_write_items.return_value = {}
        sample_order.status = OrderStatus.PAYMENT_CONFIRMED
        sample_order.payment_details = PaymentDetails(
            payment_method="credit_card",
            transaction_id="txn-123",
            payment_status="success",
            processed_at=1234567890
        )
        sample_order.status_history.append(StatusChange(
            from_status=OrderStatus.PAYMENT_PENDING,
            to_status=OrderStatus.PAYMENT_CONFIRMED,
            changed_at=1234567890,
            changed_by="user"
        ))
        
        await repo.update_status(sample_order, OrderStatus.PAYMENT_PENDING)
        
        call_args = client.transact_write_items.call_args[1]
        transact_items = call_args["TransactItems"]
        assert "payment_details" in transact_items[1]["Put"]["Item"]


class TestDeleteOrder:
    @pytest.mark.asyncio
    async def test_delete_order_success(self, order_repo, sample_order, sample_order_dict):
        repo, table, client = order_repo
        table.query.return_value = {"Items": [sample_order_dict]}
        client.transact_write_items.return_value = {}
        
        await repo.delete(sample_order.user_id, sample_order.order_id, OrderStatus.PAYMENT_PENDING)
        
        assert client.transact_write_items.call_count == 1
        call_args = client.transact_write_items.call_args[1]
        transact_items = call_args["TransactItems"]
        assert len(transact_items) == 3
        assert transact_items[0]["Delete"]["Key"]["PK"].startswith("STATUS#PAYMENT_PENDING")
        assert transact_items[1]["Delete"]["Key"]["PK"] == f"ORDERS#{sample_order.user_id}"
        assert transact_items[2]["Delete"]["Key"]["PK"] == f"ORDER#{sample_order.order_id}"

    @pytest.mark.asyncio
    async def test_delete_order_not_found(self, order_repo):
        repo, table, client = order_repo
        table.query.return_value = {"Items": []}
        
        await repo.delete("123e4567-e89b-12d3-a456-426614174000", "order-123", OrderStatus.PAYMENT_PENDING)
        
        client.transact_write_items.assert_not_called()


class TestUnmarshalOrder:
    @pytest.mark.asyncio
    async def test_unmarshal_order_with_payment_details(self, order_repo):
        repo, table, client = order_repo
        item_with_payment = {
            "order_id": "order-123",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "delivery_address": "123 Main St",
            "order_status": "PAYMENT_CONFIRMED",
            "items": [{
                "product_id": "prod-1",
                "product_name": "Product 1",
                "quantity": 2,
                "unit_price": "10.00",
                "subtotal": "20.00"
            }],
            "total_amount": "20.00",
            "created_at": 1234567890,
            "updated_at": 1234567890,
            "status_history": [],
            "payment_details": {
                "payment_method": "credit_card",
                "transaction_id": "txn-123",
                "payment_status": "success",
                "processed_at": 1234567890
            }
        }
        
        order = repo._unmarshal_order(item_with_payment)
        
        assert order.payment_details is not None
        assert order.payment_details.payment_method == "credit_card"
        assert order.payment_details.transaction_id == "txn-123"

    @pytest.mark.asyncio
    async def test_unmarshal_order_with_status_history(self, order_repo):
        repo, table, client = order_repo
        item_with_history = {
            "order_id": "order-123",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "delivery_address": "123 Main St",
            "order_status": "PAYMENT_CONFIRMED",
            "items": [{
                "product_id": "prod-1",
                "product_name": "Product 1",
                "quantity": 2,
                "unit_price": "10.00",
                "subtotal": "20.00"
            }],
            "total_amount": "20.00",
            "created_at": 1234567890,
            "updated_at": 1234567890,
            "status_history": [{
                "from_status": "PAYMENT_PENDING",
                "to_status": "PAYMENT_CONFIRMED",
                "changed_at": 1234567890,
                "changed_by": "user"
            }]
        }
        
        order = repo._unmarshal_order(item_with_history)
        
        assert len(order.status_history) == 1
        assert order.status_history[0].from_status == OrderStatus.PAYMENT_PENDING
        assert order.status_history[0].to_status == OrderStatus.PAYMENT_CONFIRMED

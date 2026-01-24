import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from app.serverful.models.models import Order, OrderStatus, OrderItem
from app.serverful.utils.errors import ApplicationError, ErrorCode


class TestCustomerOrderControllers:

    @pytest.fixture
    def mock_order_service(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_order_service):
        from fastapi import FastAPI, Request
        from app.serverful.controllers.customer_order_controllers import order_router
        from app.serverful.dependencies.dependencies import get_order_service
        from app.serverful.dependencies.auth import require_user
        from app.serverful.utils.exception_handlers import application_error_handler, general_exception_handler
        from app.serverful.utils.errors import ApplicationError

        app = FastAPI()
        
        def mock_require_user(request: Request):
            request.state.current_user = {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_name": "John",
                "role": "user"
            }

        app.include_router(order_router)
        app.add_exception_handler(ApplicationError, application_error_handler)
        app.add_exception_handler(Exception, general_exception_handler)
        app.dependency_overrides[get_order_service] = lambda: mock_order_service
        app.dependency_overrides[require_user] = mock_require_user

        return TestClient(app, raise_server_exceptions=False)

    @pytest.fixture
    def sample_order(self):
        return Order(
            order_id="order-123",
            user_id="123e4567-e89b-12d3-a456-426614174000",
            delivery_address="123 Main St",
            status=OrderStatus.PAYMENT_PENDING,
            items=[OrderItem(
                product_id="prod-1", product_name="Product 1", quantity=2,
                unit_price=Decimal("10.99"), subtotal=Decimal("21.98")
            )],
            total_amount=Decimal("21.98"),
            created_at=1704700000,
            updated_at=1704700000,
        )

    @pytest.fixture
    def valid_order_payload(self):
        return {
            "delivery_address": "123 Main St",
            "items": [{"product_id": "prod-1", "product_name": "Product 1", "quantity": 2, "unit_price": "10.99", "subtotal": "21.98"}]
        }

    @pytest.fixture
    def valid_payment_payload(self):
        return {"payment_method": "credit_card", "payment_status": "success"}

    def test_create_order_success(self, client, mock_order_service, valid_order_payload):
        mock_order_service.create_order = AsyncMock(return_value=None)
        response = client.post("/orders", json=valid_order_payload)
        assert response.status_code == 201
        assert response.json()["message"] == "Order created successfully"
        mock_order_service.create_order.assert_called_once()

    def test_create_order_user_not_found(self, client, mock_order_service, valid_order_payload):
        mock_order_service.create_order = AsyncMock(side_effect=ApplicationError(ErrorCode.USER_NOT_FOUND))
        response = client.post("/orders", json=valid_order_payload)
        assert response.status_code == 404

    @pytest.mark.parametrize("payload,description", [
        ({"items": []}, "missing delivery_address"),
        ({"delivery_address": ""}, "missing items"),
        ({"delivery_address": "123 Main St", "items": []}, "empty items list"),
        ({}, "empty payload"),
    ])
    def test_create_order_validation_errors(self, client, payload, description):
        response = client.post("/orders", json=payload)
        assert response.status_code == 422, f"Failed for case: {description}"

    def test_get_user_orders_success(self, client, mock_order_service, sample_order):
        mock_order_service.get_user_orders = AsyncMock(return_value=[sample_order])
        response = client.get("/orders")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["orders"]) == 1
        mock_order_service.get_user_orders.assert_called_once()

    def test_get_user_orders_empty(self, client, mock_order_service):
        mock_order_service.get_user_orders = AsyncMock(return_value=[])
        response = client.get("/orders")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0

    def test_get_order_by_id_success(self, client, mock_order_service, sample_order):
        mock_order_service.get_order = AsyncMock(return_value=sample_order)
        response = client.get("/orders/order-123")
        assert response.status_code == 200
        assert response.json()["order_id"] == "order-123"

    def test_get_order_by_id_not_found(self, client, mock_order_service):
        mock_order_service.get_order = AsyncMock(side_effect=ApplicationError(ErrorCode.ORDER_NOT_FOUND))
        response = client.get("/orders/nonexistent")
        assert response.status_code == 404

    def test_process_payment_success(self, client, mock_order_service, sample_order, valid_payment_payload):
        paid_order = sample_order.model_copy()
        paid_order.status = OrderStatus.PAYMENT_CONFIRMED
        mock_order_service.process_payment = AsyncMock(return_value=paid_order)
        response = client.post("/orders/order-123/payment", json=valid_payment_payload)
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.PAYMENT_CONFIRMED.value

    def test_process_payment_order_not_found(self, client, mock_order_service, valid_payment_payload):
        mock_order_service.process_payment = AsyncMock(side_effect=ApplicationError(ErrorCode.ORDER_NOT_FOUND))
        response = client.post("/orders/nonexistent/payment", json=valid_payment_payload)
        assert response.status_code == 404

    def test_process_payment_invalid_status(self, client, mock_order_service, valid_payment_payload):
        mock_order_service.process_payment = AsyncMock(side_effect=ApplicationError(ErrorCode.INVALID_ORDER_STATUS))
        response = client.post("/orders/order-123/payment", json=valid_payment_payload)
        assert response.status_code == 400

    def test_cancel_order_success(self, client, mock_order_service):
        mock_order_service.cancel_order = AsyncMock(return_value=None)
        response = client.delete("/orders/order-123")
        assert response.status_code == 200
        assert response.json()["message"] == "Order cancelled successfully"

    def test_cancel_order_not_found(self, client, mock_order_service):
        mock_order_service.cancel_order = AsyncMock(side_effect=ApplicationError(ErrorCode.ORDER_NOT_FOUND))
        response = client.delete("/orders/nonexistent")
        assert response.status_code == 404

    def test_cancel_order_cannot_be_cancelled(self, client, mock_order_service):
        mock_order_service.cancel_order = AsyncMock(side_effect=ApplicationError(ErrorCode.ORDER_CANNOT_BE_CANCELLED))
        response = client.delete("/orders/order-123")
        assert response.status_code == 400

    def test_track_order_success(self, client, mock_order_service, sample_order):
        mock_order_service.get_order = AsyncMock(return_value=sample_order)
        response = client.get("/orders/track/order-123")
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.PAYMENT_PENDING.value

    def test_track_order_not_found(self, client, mock_order_service):
        mock_order_service.get_order = AsyncMock(side_effect=ApplicationError(ErrorCode.ORDER_NOT_FOUND))
        response = client.get("/orders/track/nonexistent")
        assert response.status_code == 404

    def test_create_order_with_multiple_items(self, client, mock_order_service):
        mock_order_service.create_order = AsyncMock(return_value=None)
        payload = {
            "delivery_address": "456 Oak Ave",
            "items": [
                {"product_id": "prod-1", "product_name": "Product 1", "quantity": 2, "unit_price": "10.99", "subtotal": "21.98"},
                {"product_id": "prod-2", "product_name": "Product 2", "quantity": 1, "unit_price": "15.50", "subtotal": "15.50"}
            ]
        }
        response = client.post("/orders", json=payload)
        assert response.status_code == 201

    def test_create_order_service_error(self, client, mock_order_service, valid_order_payload):
        mock_order_service.create_order = AsyncMock(side_effect=Exception("Database error"))
        response = client.post("/orders", json=valid_order_payload)
        assert response.status_code == 500

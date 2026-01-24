import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from app.serverful.models.models import Order, OrderStatus, OrderItem
from app.serverful.utils.errors import ApplicationError, ErrorCode


class TestAdminOrderControllers:

    @pytest.fixture
    def mock_order_service(self):
        return MagicMock()

    @pytest.fixture
    def client(self, mock_order_service):
        from fastapi import FastAPI, Request
        from app.serverful.controllers.admin_order_controllers import staff_router
        from app.serverful.dependencies.dependencies import get_order_service
        from app.serverful.dependencies.auth import require_staff
        from app.serverful.utils.exception_handlers import application_error_handler, general_exception_handler
        from app.serverful.utils.errors import ApplicationError

        app = FastAPI()
        
        def mock_require_staff(request: Request):
            request.state.current_user = {
                "user_id": "223e4567-e89b-12d3-a456-426614174000",
                "user_name": "Staff",
                "role": "staff"
            }

        app.include_router(staff_router)
        app.add_exception_handler(ApplicationError, application_error_handler)
        app.add_exception_handler(Exception, general_exception_handler)
        app.dependency_overrides[get_order_service] = lambda: mock_order_service
        app.dependency_overrides[require_staff] = mock_require_staff

        return TestClient(app, raise_server_exceptions=False)

    @pytest.fixture
    def sample_order(self):
        return Order(
            order_id="order-123",
            user_id="123e4567-e89b-12d3-a456-426614174000",
            delivery_address="123 Main St",
            status=OrderStatus.PAYMENT_CONFIRMED,
            items=[OrderItem(
                product_id="prod-1", product_name="Product 1", quantity=2,
                unit_price=Decimal("10.99"), subtotal=Decimal("21.98")
            )],
            total_amount=Decimal("21.98"),
            created_at=1704700000,
            updated_at=1704700000,
        )

    def test_update_fulfilment_start_success(self, client, mock_order_service):
        mock_order_service.start_fulfilment = AsyncMock(return_value=None)
        response = client.patch("/orders/order-123/fulfilment", json={"action": "start"})
        assert response.status_code == 200
        assert response.json()["message"] == "Fulfilment started successfully"

    def test_update_fulfilment_complete_success(self, client, mock_order_service):
        mock_order_service.complete_fulfilment = AsyncMock(return_value=None)
        response = client.patch("/orders/order-123/fulfilment", json={"action": "complete"})
        assert response.status_code == 200
        assert response.json()["message"] == "Fulfilment completeed successfully"

    def test_update_fulfilment_cancel_success(self, client, mock_order_service):
        mock_order_service.cancel_fulfilment = AsyncMock(return_value=None)
        response = client.patch("/orders/order-123/fulfilment", json={"action": "cancel"})
        assert response.status_code == 200
        assert response.json()["message"] == "Fulfilment canceled successfully"

    def test_update_fulfilment_order_not_found(self, client, mock_order_service):
        mock_order_service.start_fulfilment = AsyncMock(side_effect=ApplicationError(ErrorCode.ORDER_NOT_FOUND))
        response = client.patch("/orders/nonexistent/fulfilment", json={"action": "start"})
        assert response.status_code == 404

    def test_update_fulfilment_invalid_status(self, client, mock_order_service):
        mock_order_service.start_fulfilment = AsyncMock(side_effect=ApplicationError(ErrorCode.INVALID_ORDER_STATUS))
        response = client.patch("/orders/order-123/fulfilment", json={"action": "start"})
        assert response.status_code == 400

    def test_get_all_orders_success(self, client, mock_order_service, sample_order):
        mock_order_service.get_orders_by_status = AsyncMock(return_value=[sample_order])
        response = client.get("/orders/all")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    def test_get_all_orders_empty(self, client, mock_order_service):
        mock_order_service.get_orders_by_status = AsyncMock(return_value=[])
        response = client.get("/orders/all")
        assert response.status_code == 200
        assert response.json()["total_count"] == 0

    def test_get_order_by_id_success(self, client, mock_order_service, sample_order):
        mock_order_service.get_order_by_id = AsyncMock(return_value=sample_order)
        response = client.get("/orders/order/order-123")
        assert response.status_code == 200
        assert response.json()["order_id"] == "order-123"

    def test_get_order_by_id_not_found(self, client, mock_order_service):
        mock_order_service.get_order_by_id = AsyncMock(side_effect=ApplicationError(ErrorCode.ORDER_NOT_FOUND))
        response = client.get("/orders/order/nonexistent")
        assert response.status_code == 404

    def test_get_all_orders_by_status_payment_pending(self, client, mock_order_service, sample_order):
        pending_order = sample_order.model_copy()
        pending_order.status = OrderStatus.PAYMENT_PENDING
        mock_order_service.get_orders_by_status = AsyncMock(return_value=[pending_order])
        response = client.get(f"/orders/{OrderStatus.PAYMENT_PENDING.value}")
        assert response.status_code == 200
        assert response.json()["orders"][0]["status"] == OrderStatus.PAYMENT_PENDING.value

    def test_get_all_orders_by_status_payment_confirmed(self, client, mock_order_service, sample_order):
        mock_order_service.get_orders_by_status = AsyncMock(return_value=[sample_order])
        response = client.get(f"/orders/{OrderStatus.PAYMENT_CONFIRMED.value}")
        assert response.status_code == 200
        assert response.json()["orders"][0]["status"] == OrderStatus.PAYMENT_CONFIRMED.value

    def test_get_all_orders_by_status_fulfilled(self, client, mock_order_service):
        fulfilled_order = Order(
            order_id="order-456", user_id="323e4567-e89b-12d3-a456-426614174000",
            delivery_address="456 Oak Ave", status=OrderStatus.FULFILLED,
            items=[OrderItem(product_id="prod-2", product_name="Product 2", quantity=1, 
                            unit_price=Decimal("15.50"), subtotal=Decimal("15.50"))],
            total_amount=Decimal("15.50"), created_at=1704700100, updated_at=1704700200,
        )
        mock_order_service.get_orders_by_status = AsyncMock(return_value=[fulfilled_order])
        response = client.get(f"/orders/{OrderStatus.FULFILLED.value}")
        assert response.status_code == 200
        assert response.json()["orders"][0]["status"] == OrderStatus.FULFILLED.value

    def test_get_all_orders_by_status_empty(self, client, mock_order_service):
        mock_order_service.get_orders_by_status = AsyncMock(return_value=[])
        response = client.get(f"/orders/{OrderStatus.PAYMENT_PENDING.value}")
        assert response.status_code == 200
        assert response.json()["total_count"] == 0

    def test_get_all_orders_with_multiple_orders(self, client, mock_order_service, sample_order):
        order2 = sample_order.model_copy()
        order2.order_id = "order-456"
        mock_order_service.get_orders_by_status = AsyncMock(return_value=[sample_order, order2])
        response = client.get("/orders/all")
        assert response.status_code == 200
        assert response.json()["total_count"] == 2

    def test_update_fulfilment_service_error(self, client, mock_order_service):
        mock_order_service.start_fulfilment = AsyncMock(side_effect=Exception("Database error"))
        response = client.patch("/orders/order-123/fulfilment", json={"action": "start"})
        assert response.status_code == 500

    @pytest.mark.parametrize("payload,description", [
        ({}, "missing action"),
        ({"action": "invalid"}, "invalid action"),
    ])
    def test_update_fulfilment_validation_errors(self, client, payload, description):
        response = client.patch("/orders/order-123/fulfilment", json=payload)
        assert response.status_code == 422, f"Failed for case: {description}"

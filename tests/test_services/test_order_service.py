import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from app.serverful.services.order_service import OrderService
from app.serverful.models.models import Order, OrderStatus, OrderItem, PaymentDetails, StatusChange, User, NotificationEventType
from app.serverful.models.dto import CreateOrderRequest, OrderItemDTO, ProcessPaymentRequest, PaymentStatus
from app.serverful.utils.errors import ApplicationError, ErrorCode


@pytest.fixture
def mock_order_repo():
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_sns_service():
    return AsyncMock()


@pytest.fixture
def order_service(mock_order_repo, mock_user_repo, mock_sns_service):
    return OrderService(mock_order_repo, mock_user_repo, mock_sns_service)


@pytest.fixture
def sample_user():
    return User(
        user_id="123e4567-e89b-12d3-a456-426614174000",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password="$2b$12$hashedpassword",
        created_at=1234567890,
        updated_at=1234567890
    )


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
def create_order_request():
    return CreateOrderRequest(
        delivery_address="123 Main St",
        items=[OrderItemDTO(
            product_id="prod-1",
            product_name="Product 1",
            quantity=2,
            unit_price=Decimal("10.00"),
            subtotal=Decimal("20.00")
        )]
    )


@pytest.fixture
def payment_request():
    return ProcessPaymentRequest(
        payment_method="credit_card",
        payment_status=PaymentStatus.SUCCESS
    )


class TestCreateOrder:
    @pytest.mark.asyncio
    async def test_create_order_success(self, order_service, mock_order_repo, mock_user_repo, mock_sns_service, sample_user, create_order_request):
        mock_user_repo.get_by_id.return_value = sample_user
        mock_order_repo.create.return_value = None
        mock_sns_service.publish_event.return_value = None
        
        await order_service.create_order(sample_user.user_id, create_order_request)
        
        mock_user_repo.get_by_id.assert_called_once_with(sample_user.user_id)
        assert mock_order_repo.create.call_count == 1
        created_order = mock_order_repo.create.call_args[0][0]
        assert created_order.user_id == sample_user.user_id
        assert created_order.status == OrderStatus.PAYMENT_PENDING
        assert len(created_order.items) == 1
        assert created_order.total_amount == Decimal("20.00")
        mock_sns_service.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_order_user_not_found(self, order_service, mock_user_repo, create_order_request):
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.create_order("123e4567-e89b-12d3-a456-426614174000", create_order_request)
        
        assert exc_info.value.error_code == ErrorCode.USER_NOT_FOUND


class TestCancelOrder:
    @pytest.mark.asyncio
    async def test_cancel_order_success_payment_pending(self, order_service, mock_order_repo, sample_order):
        sample_order.status = OrderStatus.PAYMENT_PENDING
        mock_order_repo.get_by_user_and_order.return_value = sample_order
        mock_order_repo.delete.return_value = None
        
        await order_service.cancel_order(sample_order.user_id, sample_order.order_id)
        
        mock_order_repo.get_by_user_and_order.assert_called_once_with(sample_order.user_id, sample_order.order_id)
        mock_order_repo.delete.assert_called_once_with(sample_order.user_id, sample_order.order_id, OrderStatus.PAYMENT_PENDING)

    @pytest.mark.asyncio
    async def test_cancel_order_success_payment_failed(self, order_service, mock_order_repo, sample_order):
        sample_order.status = OrderStatus.PAYMENT_FAILED
        mock_order_repo.get_by_user_and_order.return_value = sample_order
        mock_order_repo.delete.return_value = None
        
        await order_service.cancel_order(sample_order.user_id, sample_order.order_id)
        
        mock_order_repo.delete.assert_called_once_with(sample_order.user_id, sample_order.order_id, OrderStatus.PAYMENT_FAILED)

    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self, order_service, mock_order_repo):
        mock_order_repo.get_by_user_and_order.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.cancel_order("123e4567-e89b-12d3-a456-426614174000", "order-123")
        
        assert exc_info.value.error_code == ErrorCode.ORDER_NOT_FOUND

    @pytest.mark.asyncio
    async def test_cancel_order_invalid_status(self, order_service, mock_order_repo, sample_order):
        sample_order.status = OrderStatus.PAYMENT_CONFIRMED
        mock_order_repo.get_by_user_and_order.return_value = sample_order
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.cancel_order(sample_order.user_id, sample_order.order_id)
        
        assert exc_info.value.error_code == ErrorCode.ORDER_CANNOT_BE_CANCELLED


class TestGetOrders:
    @pytest.mark.asyncio
    async def test_get_order_by_id_success(self, order_service, mock_order_repo, sample_order):
        mock_order_repo.get_by_order_id.return_value = sample_order
        
        result = await order_service.get_order_by_id(sample_order.order_id)
        
        assert result == sample_order
        mock_order_repo.get_by_order_id.assert_called_once_with(sample_order.order_id)

    @pytest.mark.asyncio
    async def test_get_order_by_id_not_found(self, order_service, mock_order_repo):
        mock_order_repo.get_by_order_id.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.get_order_by_id("order-123")
        
        assert exc_info.value.error_code == ErrorCode.ORDER_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_order_success(self, order_service, mock_order_repo, sample_order):
        mock_order_repo.get_by_user_and_order.return_value = sample_order
        
        result = await order_service.get_order(sample_order.user_id, sample_order.order_id)
        
        assert result == sample_order
        mock_order_repo.get_by_user_and_order.assert_called_once_with(sample_order.user_id, sample_order.order_id)

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, order_service, mock_order_repo):
        mock_order_repo.get_by_user_and_order.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.get_order("123e4567-e89b-12d3-a456-426614174000", "order-123")
        
        assert exc_info.value.error_code == ErrorCode.ORDER_NOT_FOUND

    @pytest.mark.asyncio
    async def test_track_order_status_success(self, order_service, mock_order_repo, sample_order):
        mock_order_repo.get_by_order_id.return_value = sample_order
        
        result = await order_service.track_order_status(sample_order.order_id)
        
        assert result.order_id == sample_order.order_id
        assert result.status == sample_order.status
        assert result.created_at == sample_order.created_at
        assert result.updated_at == sample_order.updated_at

    @pytest.mark.asyncio
    async def test_track_order_status_not_found(self, order_service, mock_order_repo):
        mock_order_repo.get_by_order_id.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.track_order_status("order-123")
        
        assert exc_info.value.error_code == ErrorCode.ORDER_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_user_orders(self, order_service, mock_order_repo, sample_order):
        mock_order_repo.get_by_user.return_value = [sample_order]
        
        result = await order_service.get_user_orders(sample_order.user_id)
        
        assert len(result) == 1
        assert result[0] == sample_order
        mock_order_repo.get_by_user.assert_called_once_with(sample_order.user_id)

    @pytest.mark.asyncio
    async def test_get_orders_by_status_with_status(self, order_service, mock_order_repo, sample_order):
        mock_order_repo.get_by_status.return_value = [sample_order]
        
        result = await order_service.get_orders_by_status(OrderStatus.PAYMENT_PENDING)
        
        assert len(result) == 1
        assert result[0] == sample_order
        mock_order_repo.get_by_status.assert_called_once_with(OrderStatus.PAYMENT_PENDING)

    @pytest.mark.asyncio
    async def test_get_orders_by_status_without_status(self, order_service, mock_order_repo, sample_order):
        mock_order_repo.get_all.return_value = [sample_order]
        
        result = await order_service.get_orders_by_status(None)
        
        assert len(result) == 1
        assert result[0] == sample_order
        mock_order_repo.get_all.assert_called_once()


class TestProcessPayment:
    @pytest.mark.asyncio
    async def test_process_payment_success(self, order_service, mock_order_repo, mock_sns_service, sample_order, payment_request):
        mock_order_repo.get_by_user_and_order.return_value = sample_order
        mock_order_repo.update_status.return_value = None
        mock_sns_service.publish_event.return_value = None
        
        result = await order_service.process_payment(sample_order.user_id, sample_order.order_id, payment_request)
        
        assert result.status == OrderStatus.PAYMENT_CONFIRMED
        assert result.payment_details is not None
        assert result.payment_details.payment_method == "credit_card"
        assert result.payment_details.payment_status == "success"
        assert len(result.status_history) == 1
        mock_order_repo.update_status.assert_called_once()
        mock_sns_service.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_payment_failed(self, order_service, mock_order_repo, mock_sns_service, sample_order):
        mock_order_repo.get_by_user_and_order.return_value = sample_order
        mock_order_repo.update_status.return_value = None
        mock_sns_service.publish_event.return_value = None
        failed_payment = ProcessPaymentRequest(payment_method="credit_card", payment_status=PaymentStatus.FAIL)
        
        result = await order_service.process_payment(sample_order.user_id, sample_order.order_id, failed_payment)
        
        assert result.status == OrderStatus.PAYMENT_FAILED
        assert result.payment_details.payment_status == "fail"

    @pytest.mark.asyncio
    async def test_process_payment_order_not_found(self, order_service, mock_order_repo, payment_request):
        mock_order_repo.get_by_user_and_order.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.process_payment("123e4567-e89b-12d3-a456-426614174000", "order-123", payment_request)
        
        assert exc_info.value.error_code == ErrorCode.ORDER_NOT_FOUND

    @pytest.mark.asyncio
    async def test_process_payment_invalid_status(self, order_service, mock_order_repo, sample_order, payment_request):
        sample_order.status = OrderStatus.PAYMENT_CONFIRMED
        mock_order_repo.get_by_user_and_order.return_value = sample_order
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.process_payment(sample_order.user_id, sample_order.order_id, payment_request)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_ORDER_STATUS


class TestFulfillment:
    @pytest.mark.asyncio
    async def test_start_fulfilment_success(self, order_service, mock_order_repo, mock_sns_service, sample_order):
        sample_order.status = OrderStatus.PAYMENT_CONFIRMED
        mock_order_repo.get_by_order_id.return_value = sample_order
        mock_order_repo.update_status.return_value = None
        mock_sns_service.publish_event.return_value = None
        
        await order_service.start_fulfilment(sample_order.order_id)
        
        assert sample_order.status == OrderStatus.FULFILLMENT_IN_PROGRESS
        assert len(sample_order.status_history) == 1
        mock_order_repo.update_status.assert_called_once()
        mock_sns_service.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_fulfilment_order_not_found(self, order_service, mock_order_repo):
        mock_order_repo.get_by_order_id.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.start_fulfilment("order-123")
        
        assert exc_info.value.error_code == ErrorCode.ORDER_NOT_FOUND

    @pytest.mark.asyncio
    async def test_start_fulfilment_invalid_status(self, order_service, mock_order_repo, sample_order):
        sample_order.status = OrderStatus.PAYMENT_PENDING
        mock_order_repo.get_by_order_id.return_value = sample_order
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.start_fulfilment(sample_order.order_id)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_ORDER_STATUS

    @pytest.mark.asyncio
    async def test_complete_fulfilment_success(self, order_service, mock_order_repo, mock_sns_service, sample_order):
        sample_order.status = OrderStatus.FULFILLMENT_IN_PROGRESS
        mock_order_repo.get_by_order_id.return_value = sample_order
        mock_order_repo.update_status.return_value = None
        mock_sns_service.publish_event.return_value = None
        
        await order_service.complete_fulfilment(sample_order.order_id)
        
        assert sample_order.status == OrderStatus.FULFILLED
        assert len(sample_order.status_history) == 1
        mock_order_repo.update_status.assert_called_once()
        mock_sns_service.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_fulfilment_order_not_found(self, order_service, mock_order_repo):
        mock_order_repo.get_by_order_id.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.complete_fulfilment("order-123")
        
        assert exc_info.value.error_code == ErrorCode.ORDER_NOT_FOUND

    @pytest.mark.asyncio
    async def test_complete_fulfilment_invalid_status(self, order_service, mock_order_repo, sample_order):
        sample_order.status = OrderStatus.PAYMENT_CONFIRMED
        mock_order_repo.get_by_order_id.return_value = sample_order
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.complete_fulfilment(sample_order.order_id)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_ORDER_STATUS

    @pytest.mark.asyncio
    async def test_cancel_fulfilment_success(self, order_service, mock_order_repo, mock_sns_service, sample_order):
        sample_order.status = OrderStatus.FULFILLMENT_IN_PROGRESS
        mock_order_repo.get_by_order_id.return_value = sample_order
        mock_order_repo.update_status.return_value = None
        mock_sns_service.publish_event.return_value = None
        
        await order_service.cancel_fulfilment(sample_order.order_id)
        
        assert sample_order.status == OrderStatus.FULFILLMENT_FAILED
        assert len(sample_order.status_history) == 1
        mock_order_repo.update_status.assert_called_once()
        mock_sns_service.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_fulfilment_order_not_found(self, order_service, mock_order_repo):
        mock_order_repo.get_by_order_id.return_value = None
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.cancel_fulfilment("order-123")
        
        assert exc_info.value.error_code == ErrorCode.ORDER_NOT_FOUND

    @pytest.mark.asyncio
    async def test_cancel_fulfilment_invalid_status(self, order_service, mock_order_repo, sample_order):
        sample_order.status = OrderStatus.PAYMENT_CONFIRMED
        mock_order_repo.get_by_order_id.return_value = sample_order
        
        with pytest.raises(ApplicationError) as exc_info:
            await order_service.cancel_fulfilment(sample_order.order_id)
        
        assert exc_info.value.error_code == ErrorCode.INVALID_ORDER_STATUS

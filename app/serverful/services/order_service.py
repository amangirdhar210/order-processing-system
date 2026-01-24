from typing import List, Optional
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from app.serverful.models.dto import CreateOrderRequest, ProcessPaymentRequest, OrderDTO, OrderStatusResponse, OrderItemDTO, PaymentDetailsDTO
from app.serverful.models.models import OrderStatus, Order, OrderItem, PaymentDetails, StatusChange, NotificationEvent, NotificationEventType
from app.serverful.utils.errors import ApplicationError, ErrorCode


class OrderService:
    def __init__(self, order_repository, user_repository, sns_service) -> None:
        self.order_repo = order_repository
        self.user_repo = user_repository
        self.sns_service = sns_service

    async def create_order(self, order_req: CreateOrderRequest) -> None:
        user = await self.user_repo.get_by_id(order_req.user_id)
        if not user:
            raise ApplicationError(ErrorCode.USER_NOT_FOUND)
        
        order_id = str(uuid.uuid4())
        now = self._current_timestamp()
        
        items = [self._map_order_item(item) for item in order_req.items]
        total = sum(item.subtotal for item in items)
        
        order = Order(
            order_id=order_id,
            user_id=order_req.user_id,
            delivery_address=order_req.delivery_address,
            status=OrderStatus.PAYMENT_PENDING,
            items=items,
            total_amount=total,
            created_at=now,
            updated_at=now
        )
        
        await self.order_repo.create(order)
        await self._publish_event(NotificationEventType.ORDER_CREATED, order_id, order_req.user_id)

    async def cancel_order(self, user_id: str, order_id: str) -> None:
        order = await self.order_repo.get_by_user_and_order(user_id, order_id)
        if not order:
            raise ApplicationError(ErrorCode.ORDER_NOT_FOUND)
        
        if order.status not in [OrderStatus.PAYMENT_PENDING, OrderStatus.PAYMENT_FAILED]:
            raise ApplicationError(ErrorCode.ORDER_CANNOT_BE_CANCELLED)
        
        await self.order_repo.delete(user_id, order_id, order.status)

    async def get_order_by_id(self, order_id: str) -> OrderDTO:
        order = await self.order_repo.get_by_order_id(order_id)
        if not order:
            raise ApplicationError(ErrorCode.ORDER_NOT_FOUND)
        
        return self._map_order_dto(order)

    async def track_order_status(self, order_id: str) -> OrderStatusResponse:
        order = await self.order_repo.get_by_order_id(order_id)
        if not order:
            raise ApplicationError(ErrorCode.ORDER_NOT_FOUND)
        
        return OrderStatusResponse(
            order_id=order.order_id,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at
        )

    async def get_user_orders(self, user_id: str) -> List[OrderDTO]:
        orders = await self.order_repo.get_by_user(user_id)
        return [self._map_order_dto(order) for order in orders]

    async def get_orders_by_status(self, status: Optional[OrderStatus]) -> List[OrderDTO]:
        if status:
            orders = await self.order_repo.get_by_status(status)
        else:
            orders = await self.order_repo.get_all()
        return [self._map_order_dto(order) for order in orders]

    async def process_payment(self, user_id: str, order_id: str, payment_req: ProcessPaymentRequest) -> OrderDTO:
        order = await self.order_repo.get_by_user_and_order(user_id, order_id)
        if not order:
            raise ApplicationError(ErrorCode.ORDER_NOT_FOUND)
        
        if order.status != OrderStatus.PAYMENT_PENDING:
            raise ApplicationError(ErrorCode.INVALID_ORDER_STATUS)
        
        is_success = payment_req.payment_status.value == "success"
        new_status = OrderStatus.PAYMENT_CONFIRMED if is_success else OrderStatus.PAYMENT_FAILED
        event_type = NotificationEventType.PAYMENT_CONFIRMED if is_success else NotificationEventType.PAYMENT_FAILED
        
        now = self._current_timestamp()
        payment_details = PaymentDetails(
            payment_method=payment_req.payment_method,
            transaction_id=str(uuid.uuid4()),
            payment_status=payment_req.payment_status.value,
            processed_at=now
        )
        
        status_change = StatusChange(
            from_status=order.status,
            to_status=new_status,
            changed_at=now,
            changed_by=user_id
        )
        
        order.status = new_status
        order.payment_details = payment_details
        order.status_history.append(status_change)
        order.updated_at = now
        
        await self.order_repo.update_status(order, OrderStatus.PAYMENT_PENDING)
        await self._publish_event(event_type, order_id, user_id)
        
        return self._map_order_dto(order)

    async def start_fulfilment(self, order_id: str) -> None:
        order = await self.order_repo.get_by_order_id(order_id)
        if not order:
            raise ApplicationError(ErrorCode.ORDER_NOT_FOUND)
        
        if order.status != OrderStatus.PAYMENT_CONFIRMED:
            raise ApplicationError(ErrorCode.INVALID_ORDER_STATUS)
        
        await self._update_order_status(order, OrderStatus.FULFILLMENT_IN_PROGRESS, "system")
        await self._publish_event(NotificationEventType.FULFILLMENT_STARTED, order_id, order.user_id)

    async def complete_fulfilment(self, order_id: str) -> None:
        order = await self.order_repo.get_by_order_id(order_id)
        if not order:
            raise ApplicationError(ErrorCode.ORDER_NOT_FOUND)
        
        if order.status != OrderStatus.FULFILLMENT_IN_PROGRESS:
            raise ApplicationError(ErrorCode.INVALID_ORDER_STATUS)
        
        await self._update_order_status(order, OrderStatus.FULFILLED, "system")
        await self._publish_event(NotificationEventType.FULFILLED, order_id, order.user_id)

    async def cancel_fulfilment(self, order_id: str) -> None:
        order = await self.order_repo.get_by_order_id(order_id)
        if not order:
            raise ApplicationError(ErrorCode.ORDER_NOT_FOUND)
        
        if order.status != OrderStatus.FULFILLMENT_IN_PROGRESS:
            raise ApplicationError(ErrorCode.INVALID_ORDER_STATUS)
        
        await self._update_order_status(order, OrderStatus.FULFILLMENT_FAILED, "system")
        await self._publish_event(NotificationEventType.FULFILLMENT_CANCELLED, order_id, order.user_id)

    async def _update_order_status(self, order: Order, new_status: OrderStatus, changed_by: str) -> None:
        old_status = order.status
        now = self._current_timestamp()
        
        status_change = StatusChange(
            from_status=old_status,
            to_status=new_status,
            changed_at=now,
            changed_by=changed_by
        )
        
        order.status = new_status
        order.status_history.append(status_change)
        order.updated_at = now
        
        await self.order_repo.update_status(order, old_status)

    async def _publish_event(self, event_type: NotificationEventType, order_id: str, user_id: str) -> None:
        event = NotificationEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            order_id=order_id,
            user_id=user_id,
            occurred_at=self._current_timestamp()
        )
        await self.sns_service.publish_event(event)

    def _map_order_item(self, item_dto: OrderItemDTO) -> OrderItem:
        return OrderItem(
            product_id=item_dto.product_id,
            product_name=item_dto.product_name,
            quantity=item_dto.quantity,
            unit_price=item_dto.unit_price,
            subtotal=item_dto.subtotal
        )

    def _map_order_dto(self, order: Order) -> OrderDTO:
        items = [OrderItemDTO(
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.subtotal
        ) for item in order.items]
        
        payment_dto = None
        if order.payment_details:
            payment_dto = PaymentDetailsDTO(
                payment_method=order.payment_details.payment_method,
                transaction_id=order.payment_details.transaction_id,
                payment_status=order.payment_details.payment_status,
                processed_at=order.payment_details.processed_at
            )
        
        return OrderDTO(
            order_id=order.order_id,
            user_id=order.user_id,
            delivery_address=order.delivery_address,
            status=order.status,
            items=items,
            total_amount=order.total_amount,
            payment_details=payment_dto,
            created_at=order.created_at,
            updated_at=order.updated_at
        )

    def _current_timestamp(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())
from fastapi import APIRouter, Depends, status
from app.serverful.models.dto import UpdateFulfilmentRequest, OrderDTO, OrderListResponse, GenericResponse
from app.serverful.models.models import OrderStatus
from app.serverful.dependencies.auth import require_staff
from app.serverful.dependencies.dependencies import OrderServiceInstance

staff_router = APIRouter(prefix="/orders", dependencies=[Depends(require_staff)])

@staff_router.patch("/{order_id}/fulfilment", response_model=GenericResponse, status_code=status.HTTP_200_OK)
async def update_fulfilment(
    order_id: str,
    fulfilment_request: UpdateFulfilmentRequest,
    order_service: OrderServiceInstance,
) -> GenericResponse:
    """Update fulfilment status of an order"""
    action = fulfilment_request.action
    
    action_map = {
        "start": order_service.start_fulfilment,
        "complete": order_service.complete_fulfilment,
        "cancel": order_service.cancel_fulfilment,
    }
    
    await action_map[action](order_id)
    
    return GenericResponse(message=f"Fulfilment {action}ed successfully")

@staff_router.get("/all", response_model=OrderListResponse, status_code=status.HTTP_200_OK)
async def get_all_orders(
    order_service: OrderServiceInstance,
) -> OrderListResponse:
    """Get all orders across all users"""
    orders = await order_service.get_orders_by_status(None)
    return OrderListResponse(orders=orders, total_count=len(orders))

@staff_router.get("/order/{order_id}", response_model=OrderDTO, status_code=status.HTTP_200_OK)
async def get_order_by_id(
    order_id: str,
    order_service: OrderServiceInstance,
) -> OrderDTO:
    """Get order details by order ID without user ID"""
    return await order_service.get_order_by_id(order_id)

@staff_router.get("/{order_status}", response_model=OrderListResponse, status_code=status.HTTP_200_OK)
async def get_all_orders_by_status(
    order_status: OrderStatus,
    order_service: OrderServiceInstance,
) -> OrderListResponse:
    """Get all orders filtered by status"""
    orders = await order_service.get_orders_by_status(order_status)
    return OrderListResponse(orders=orders, total_count=len(orders))

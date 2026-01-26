from fastapi import APIRouter, Depends, status
from app.serverful.models.dto import UpdateFulfilmentRequest, GenericResponse
from app.serverful.models.models import OrderStatus, Order
from app.serverful.dependencies.auth import require_staff
from app.serverful.dependencies.dependencies import OrderServiceInstance
from typing import List
from pydantic import BaseModel

class OrderListResponse(BaseModel):
    orders: List[Order]
    total_count: int

staff_router = APIRouter(dependencies=[Depends(require_staff)])

@staff_router.patch("/orders/{order_id}/fulfilment", response_model=GenericResponse, status_code=status.HTTP_200_OK)
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
    
    action_verb_map = {
        "start": "started",
        "complete": "completed",
        "cancel": "cancelled",
    }
    
    await action_map[action](order_id)
    
    return GenericResponse(message=f"Fulfilment {action_verb_map[action]} successfully")

@staff_router.get("/orders/all", response_model=OrderListResponse, status_code=status.HTTP_200_OK)
async def get_all_orders(
    order_service: OrderServiceInstance,
) -> OrderListResponse:
    """Get all orders across all users"""
    orders = await order_service.get_orders_by_status(None)
    return OrderListResponse(orders=orders, total_count=len(orders))

@staff_router.get("/orders/order/{order_id}", response_model=Order, status_code=status.HTTP_200_OK)
async def get_order_by_id(
    order_id: str,
    order_service: OrderServiceInstance,
) -> Order:
    """Get order details by order ID without user ID"""
    return await order_service.get_order_by_id(order_id)

@staff_router.get("/orders/{order_status}", response_model=OrderListResponse, status_code=status.HTTP_200_OK)
async def get_all_orders_by_status(
    order_status: OrderStatus,
    order_service: OrderServiceInstance,
) -> OrderListResponse:
    """Get all orders filtered by status"""
    orders = await order_service.get_orders_by_status(order_status)
    return OrderListResponse(orders=orders, total_count=len(orders))

from fastapi import APIRouter, Depends, Request, status
from app.serverful.models.dto import CreateOrderRequest, ProcessPaymentRequest, GenericResponse
from app.serverful.models.models import Order
from app.serverful.dependencies.auth import require_user
from app.serverful.dependencies.dependencies import OrderServiceInstance
from typing import List
from pydantic import BaseModel

class OrderListResponse(BaseModel):
    orders: List[Order]
    total_count: int

order_router = APIRouter(prefix="/orders", dependencies=[Depends(require_user)])

@order_router.post("", response_model=GenericResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: Request,
    order_request: CreateOrderRequest,
    order_service: OrderServiceInstance,
) -> GenericResponse:
    """Create a new order for the authenticated user"""
    user_id = request.state.current_user["user_id"]
    await order_service.create_order(user_id, order_request)
    return GenericResponse(message="Order created successfully")

@order_router.get("", response_model=OrderListResponse, status_code=status.HTTP_200_OK)
async def get_user_orders(
    request: Request,
    order_service: OrderServiceInstance,
) -> OrderListResponse:
    """Get all orders for the authenticated user"""
    user_id = request.state.current_user["user_id"]
    orders = await order_service.get_user_orders(user_id)
    return OrderListResponse(orders=orders, total_count=len(orders))

@order_router.get("/{order_id}", response_model=Order, status_code=status.HTTP_200_OK)
async def get_order_by_id(
    request: Request,
    order_id: str,
    order_service: OrderServiceInstance,
) -> Order:
    """Get a specific order by ID for the authenticated user"""
    user_id = request.state.current_user["user_id"]
    return await order_service.get_order(user_id, order_id)

@order_router.post("/{order_id}/payment", response_model=Order, status_code=status.HTTP_200_OK)
async def process_payment(
    request: Request,
    order_id: str,
    payment_request: ProcessPaymentRequest,
    order_service: OrderServiceInstance,
) -> Order:
    """Process payment for an order"""
    user_id = request.state.current_user["user_id"]
    return await order_service.process_payment(user_id, order_id, payment_request)

@order_router.delete("/{order_id}", response_model=GenericResponse, status_code=status.HTTP_200_OK)
async def cancel_order(
    request: Request,
    order_id: str,
    order_service: OrderServiceInstance,
) -> GenericResponse:
    """Cancel an order by ID for the authenticated user"""
    user_id = request.state.current_user["user_id"]
    await order_service.cancel_order(user_id, order_id)
    return GenericResponse(message="Order cancelled successfully")

@order_router.get("/track/{order_id}", response_model=Order, status_code=status.HTTP_200_OK)
async def track_order(
    request: Request,
    order_id: str,
    order_service: OrderServiceInstance,
) -> Order:
    """Track order by verifying user ownership"""
    user_id = request.state.current_user["user_id"]
    return await order_service.get_order(user_id, order_id)


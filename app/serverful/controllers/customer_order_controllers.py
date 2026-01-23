from fastapi import APIRouter, Depends, Request, status
from app.serverful.models.dto import CreateOrderRequest, OrderDTO, OrderListResponse, GenericResponse
from app.serverful.dependencies.auth import require_user
from app.serverful.dependencies.dependencies import OrderServiceInstance

order_router = APIRouter(prefix="/orders", dependencies=[Depends(require_user)])

@order_router.post("", response_model=GenericResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: Request,
    order_request: CreateOrderRequest,
    order_service: OrderServiceInstance,
) -> GenericResponse:
    """Create a new order for the authenticated user"""
    pass

@order_router.get("", response_model=OrderListResponse, status_code=status.HTTP_200_OK)
async def get_user_orders(
    request: Request,
    order_service: OrderServiceInstance,
) -> OrderListResponse:
    """Get all orders for the authenticated user"""
    pass

@order_router.get("/{order_id}", response_model=OrderDTO, status_code=status.HTTP_200_OK)
async def get_order_by_id(
    request: Request,
    order_id: str,
    order_service: OrderServiceInstance,
) -> OrderDTO:
    """Get a specific order by ID for the authenticated user"""
    pass

@order_router.delete("/{order_id}", response_model=GenericResponse, status_code=status.HTTP_200_OK)
async def cancel_order(
    request: Request,
    order_id: str,
    order_service: OrderServiceInstance,
) -> GenericResponse:
    """Cancel an order by ID for the authenticated user"""
    pass


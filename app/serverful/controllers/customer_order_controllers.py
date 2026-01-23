from fastapi import APIRouter

order_router = APIRouter(prefix="/orders")

@order_router.post("")
async def create_order():
    pass

@order_router.get("")
async def get_user_orders():
    pass

@order_router.get("/{order_id}")
async def get_order_by_id(order_id: str):
    pass

@order_router.delete("/{order_id}")
async def cancel_order(order_id: str):
    pass


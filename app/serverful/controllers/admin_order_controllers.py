from fastapi import APIRouter

staff_router = APIRouter(prefix="/orders")

@staff_router.post("/{order_id}/payment")
async def process_payment(order_id: str):
    pass

@staff_router.patch("/{order_id}/fulfilment")
async def update_fulfilment(order_id: str):
    pass

@staff_router.get("/all")
async def get_all_orders():
    pass

@staff_router.get("/{order_status}")
async def get_all_orders_by_status():
    pass

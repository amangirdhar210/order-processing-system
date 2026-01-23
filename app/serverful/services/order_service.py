class OrderService:
    def __init__(self, order_repository, user_repository, sns_service):
        pass

    async def create_order(self, order_req):
        pass

    async def cancel_order(self,user_id, order_id):
        pass

    async def get_order_by_id(self, order_id):
        pass

    async def track_order_status(self, order_id):
        pass

    async def get_user_orders(self, user_id):
        pass

    async def get_orders_by_status(self, status):
        pass

    async def confirm_payment(self, order_id, payment_req):
        pass

    async def fail_payment(self, order_id, payment_req):
        pass

    async def start_fulfilment(self, order_id):
        pass

    async def complete_fulfilment(self, order_id):
        pass 

    async def cancel_fulfilment(self, order_id):
        pass
class OrderRepository:

    def __init__(self, dynamodb_resource, table_name):
        self.dynamodb_resource= dynamodb_resource
        self.table= dynamodb_resource.Table(table_name)


    async def create(self, order):
        pass 

    async def get_by_user_and_order_id(self, user_id, order_id):
        pass


    async def get_by_order_id(self, order_id):
        pass


    async def get_orders_by_user_id(self, user_id):
        pass

    async def get_orders_by_status(self, status):
        pass

    async def update_order_status(self):
        pass

    def _unmarshal_order(self, item):
        pass
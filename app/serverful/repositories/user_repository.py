class UserRepository:
    def __init__(self, dynamodb_resource, table_name):
        self.dynamodb_resource= dynamodb_resource
        self.table= dynamodb_resource.Table(table_name)


    async def create(self, user):
        pass

    async def get_by_email(self, email):
        pass

    async def get_by_id(self, user_id):
        pass 


class AuthService:

    def __init__(self,user_repository):
        self.user_repo=user_repository 

    async def register_user(self, user_request):
        pass 

    async def login_user(self, login_request):
        pass
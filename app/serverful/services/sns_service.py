class SnsService:

    def __init__(self, sns_client):
        self.sns_client= sns_client

    async def publish_event(self, event):
        pass
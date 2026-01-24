from pydantic import BaseModel, Field


class OrderNotificationMessage(BaseModel):
    event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    occurred_at: int = Field(gt=0)
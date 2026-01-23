from pydantic import BaseModel,Field, field_validator 
from enum import Enum 

class OrderStatus(str, Enum):
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    FULFILLMENT_IN_PROGRESS = "FULFILLMENT_IN_PROGRESS"
    FULFILLED = "FULFILLED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    FULFILLMENT_FAILED = "FULFILLMENT_FAILED"

class NotificationEventType(str,Enum):
    ORDER_CREATED= "ORDER_CREATED"
    PAYMENT_CONFIRMED= "PAYMENT_CONFIRMED"
    FULFILLMENT_STARTED="FULFILLMENT_STARTED"
    FULFILLED= "FULFILLED"
    PAYMENT_FAILED= "PAYMENT_FAILED"
    FULFILLMENT_CANCELLED= "FULFILLMENT_CANCELED"

class User(BaseModel):
    user_id:str=Field(min_length=32, max_length=40)
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    created_at: int=Field(ge=0,default=0)
    updated_at: int =Field(ge=0,default=0)

class OrderItem(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    product_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(gt=0, le=1000)
    unit_price: Decimal = Field(gt=0, decimal_places=2)
    subtotal: Decimal = Field(gt=0, decimal_places=2)

    @field_validator("subtotal")
    @classmethod
    def validate_subtotal(cls, subtotal_value: Decimal, info) -> Decimal:
        if "quantity" in info.data and "unit_price" in info.data:
            quantity = info.data["quantity"]
            unit_price = info.data["unit_price"]
            expected = Decimal(str(quantity)) * unit_price
            tolerance = Decimal("0.01")
            if abs(subtotal_value - expected) > tolerance:
                raise ValueError("subtotal must equal quantity * unit_price")
        return subtotal_value

class PaymentDetails(BaseModel):
    payment_method: str = Field(min_length=1, max_length=50)
    transaction_id: str = Field(min_length=1, max_length=100)
    payment_status: str = Field(min_length=1, max_length=50)
    processed_at: Optional[int] = None

class StatusChange(BaseModel):
    from_status: OrderStatus
    to_status: OrderStatus
    changed_at: int = Field(gt=0)
    changed_by: str = Field(min_length=1, max_length=100)

class Order(BaseModel):
    order_id: str = ""
    user_id: str = Field(min_length=1, max_length=100)
    delivery_address: str = Field(min_length=10, max_length=500)
    status: OrderStatus
    items: List[OrderItem] = Field(min_length=1)
    total_amount: Decimal = Field(gt=0, decimal_places=2)
    payment_details: Optional[PaymentDetails] = None
    status_history: List[StatusChange] = []
    created_at: int = 0
    updated_at: int = 0

    @field_validator("total_amount")
    @classmethod
    def validate_total(cls, total_value: Decimal, info) -> Decimal:
        if "items" in info.data:
            items = info.data["items"]
            calculated = sum(item.subtotal for item in items)
            tolerance = Decimal("0.01")
            if abs(total_value - calculated) > tolerance:
                raise ValueError("total_amount must equal sum of item subtotals")
        return total_value


class NotificationEvent(BaseModel):
    event_id: str = ""
    event_type: NotificationEventType
    order_id: str = Field(min_length=1, max_length=100)
    user_id: str = Field(min_length=1, max_length=100)
    occurred_at: int = Field(gt=0)
    metadata: dict = {} 
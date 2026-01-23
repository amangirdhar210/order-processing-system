from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from decimal import Decimal
from app.serverful.models.models import OrderStatus


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class RegisterUserRequest(BaseModel):
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class UserDTO(BaseModel):
    id: str = Field(min_length=1)
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    created_at: int = Field(gt=0)
    updated_at: int = Field(gt=0)


class LoginUserResponse(BaseModel):
    token: str = Field(min_length=1)
    user: UserDTO


class OrderItemDTO(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    product_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(gt=0, le=1000)
    unit_price: Decimal = Field(gt=0, decimal_places=2)
    subtotal: Decimal = Field(gt=0, decimal_places=2)

    @field_validator("subtotal")
    @classmethod
    def validate_subtotal_matches_calculation(cls, subtotal_value: Decimal, info) -> Decimal:
        if "quantity" in info.data and "unit_price" in info.data:
            quantity = info.data["quantity"]
            unit_price = info.data["unit_price"]
            expected_subtotal = Decimal(str(quantity)) * unit_price
            tolerance = Decimal("0.01")
            
            if abs(subtotal_value - expected_subtotal) > tolerance:
                raise ValueError("subtotal must equal quantity * unit_price")
        
        return subtotal_value


class CreateOrderRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    delivery_address: str = Field(min_length=10, max_length=500)
    items: List[OrderItemDTO] = Field(min_items=1)

    @field_validator("items")
    @classmethod
    def validate_items_not_empty(cls, items: List[OrderItemDTO]) -> List[OrderItemDTO]:
        if not items:
            raise ValueError("Order must contain at least one item")
        return items


class ConfirmPaymentRequest(BaseModel):
    payment_method: str = Field(min_length=1, max_length=50)


class PaymentDetailsDTO(BaseModel):
    payment_method: str
    transaction_id: str
    payment_status: str
    processed_at: Optional[int] = None


class OrderDTO(BaseModel):
    order_id: str
    user_id: str
    delivery_address: str
    status: OrderStatus
    items: List[OrderItemDTO]
    total_amount: Decimal
    payment_details: Optional[PaymentDetailsDTO] = None
    created_at: int
    updated_at: int


class GenericResponse(BaseModel):
    message: str


class UpdateFulfilmentRequest(BaseModel):
    action: str = Field(pattern="^(start|complete|cancel)$")


class OrderListResponse(BaseModel):
    orders: List[OrderDTO]
    total_count: int


class OrderStatusResponse(BaseModel):
    order_id: str
    status: OrderStatus
    created_at: int
    updated_at: int

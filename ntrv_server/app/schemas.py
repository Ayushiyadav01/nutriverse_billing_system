from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.models import OrderMode, PaymentMode, DiscountType


# Menu Item Schemas
class MenuItemBase(BaseModel):
    code: str
    name: str
    category: str
    price: Decimal
    cost: Decimal
    is_active: bool = True


class MenuItemCreate(MenuItemBase):
    @field_validator('price', 'cost')
    @classmethod
    def validate_positive_amount(cls, v):
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if not v:
            raise ValueError("Code cannot be empty")
        return v.upper()


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    is_active: Optional[bool] = None
    
    @field_validator('price', 'cost')
    @classmethod
    def validate_positive_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError("Amount cannot be negative")
        return v


class MenuItem(MenuItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Order Item Schemas
class OrderItemBase(BaseModel):
    menu_item_id: Optional[int] = None
    menu_item_code: Optional[str] = None
    qty: int
    
    @field_validator('qty')
    @classmethod
    def validate_qty(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v
    
    @model_validator(mode='after')
    def validate_item_reference(self):
        if self.menu_item_id is None and self.menu_item_code is None:
            raise ValueError("Either menu_item_id or menu_item_code must be provided")
        return self


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(BaseModel):
    id: int
    menu_item_id: int
    item_name: str
    qty: int
    unit_price: Decimal
    line_total: Decimal
    unit_cost: Decimal
    line_cost: Decimal
    
    model_config = ConfigDict(from_attributes=True)


# Order Schemas
class DiscountInfo(BaseModel):
    type: DiscountType = DiscountType.NONE
    value: Decimal = Decimal('0')
    
    @model_validator(mode='after')
    def validate_discount_value(self):
        if self.value < 0:
            raise ValueError("Discount value cannot be negative")
        
        if self.type == DiscountType.PERCENT and self.value > 100:
            raise ValueError("Percentage discount cannot exceed 100%")
        
        return self


class OrderBase(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    mode_of_order: OrderMode = OrderMode.IN_PERSON
    payment_mode: PaymentMode = PaymentMode.CASH
    notes: Optional[str] = None
    tax_percent: Decimal = Decimal('0')
    other_costs: Decimal = Decimal('0')
    
    @field_validator('tax_percent', 'other_costs')
    @classmethod
    def validate_positive_amount(cls, v):
        if v < 0:
            raise ValueError("Amount cannot be negative")
        return v


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]
    discount: DiscountInfo = Field(default_factory=lambda: DiscountInfo())
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError("Order must contain at least one item")
        return v


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    mode_of_order: Optional[OrderMode] = None
    payment_mode: Optional[PaymentMode] = None
    notes: Optional[str] = None


class Order(BaseModel):
    id: int
    order_number: str
    timestamp: datetime
    customer_name: Optional[str]
    phone: Optional[str]
    mode_of_order: OrderMode
    payment_mode: PaymentMode
    notes: Optional[str]
    
    subtotal: Decimal
    discount_type: DiscountType
    discount_value: Decimal
    discount_amount: Decimal
    tax_percent: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    
    total_making_cost: Decimal
    other_costs: Decimal
    net_amount: Decimal
    total_profit: Decimal
    
    created_at: datetime
    items: List[OrderItem]
    
    model_config = ConfigDict(from_attributes=True)


class OrderSummary(BaseModel):
    id: int
    order_number: str
    timestamp: datetime
    customer_name: Optional[str]
    total_amount: Decimal
    payment_mode: PaymentMode
    
    model_config = ConfigDict(from_attributes=True)


# Analytics Schemas
class DateRangeParams(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class AnalyticsSummary(BaseModel):
    total_orders: int
    total_sales: Decimal
    total_making_cost: Decimal
    total_profit: Decimal
    average_order_value: Decimal


class TopSellingItem(BaseModel):
    item_name: str
    category: str
    total_qty: int
    total_sales: Decimal


class SalesByTimeUnit(BaseModel):
    time_unit: str  # day, week, month, hour
    sales: Decimal
    orders_count: int


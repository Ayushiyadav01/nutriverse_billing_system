from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.models import OrderMode, PaymentMode, DiscountType, FoodPreparationStage, PaymentStatus, ExpenseType


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
    sold_price: Optional[Decimal] = None  # Optional sold price (overrides MRP if provided)
    
    @field_validator('sold_price')
    @classmethod
    def validate_sold_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("Sold price cannot be negative")
        return v


class OrderItem(BaseModel):
    id: int
    menu_item_id: int
    item_name: str
    qty: int
    unit_price: Decimal  # MRP
    unit_sold_price: Optional[Decimal] = None  # Actual sold price
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
    food_preparation_stage: FoodPreparationStage = FoodPreparationStage.ORDERED
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
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
    food_preparation_stage: Optional[FoodPreparationStage] = None
    payment_status: Optional[PaymentStatus] = None


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
    
    food_preparation_stage: FoodPreparationStage
    payment_status: PaymentStatus
    payment_completed_at: Optional[datetime]
    
    created_at: datetime
    items: List[OrderItem]
    
    @field_validator('mode_of_order', mode='before')
    @classmethod
    def validate_mode_of_order(cls, v):
        if v is None:
            return OrderMode.IN_PERSON
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == 'in_person':
                return OrderMode.IN_PERSON
            elif v_lower == 'phone':
                return OrderMode.PHONE
            elif v_lower == 'whatsapp':
                return OrderMode.WHATSAPP
            elif v_lower == 'streamlit_ui':
                return OrderMode.STREAMLIT_UI
        return v
    
    @field_validator('payment_mode', mode='before')
    @classmethod
    def validate_payment_mode(cls, v):
        if v is None:
            return PaymentMode.CASH
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == 'cash':
                return PaymentMode.CASH
            elif v_lower == 'card':
                return PaymentMode.CARD
            elif v_lower == 'upi':
                return PaymentMode.UPI
            elif v_lower == 'wallet':
                return PaymentMode.WALLET
        return v
    
    @field_validator('discount_type', mode='before')
    @classmethod
    def validate_discount_type(cls, v):
        if v is None:
            return DiscountType.NONE
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == 'none':
                return DiscountType.NONE
            elif v_lower == 'percent':
                return DiscountType.PERCENT
            elif v_lower == 'flat':
                return DiscountType.FLAT
        return v
    
    @field_validator('food_preparation_stage', mode='before')
    @classmethod
    def validate_food_stage(cls, v):
        if v is None:
            return FoodPreparationStage.ORDERED
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == 'ordered':
                return FoodPreparationStage.ORDERED
            elif v_lower == 'preparing':
                return FoodPreparationStage.PREPARING
            elif v_lower == 'completed':
                return FoodPreparationStage.COMPLETED
        return v
    
    @field_validator('payment_status', mode='before')
    @classmethod
    def validate_payment_status(cls, v):
        if v is None:
            return PaymentStatus.PENDING
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == 'pending':
                return PaymentStatus.PENDING
            elif v_lower == 'due':
                return PaymentStatus.DUE
            elif v_lower == 'payment_done':
                return PaymentStatus.PAYMENT_DONE
            elif v_lower == 'overpaid':
                return PaymentStatus.OVERPAID
            elif v_lower == 'adjusted':
                return PaymentStatus.ADJUSTED
        return v
    
    model_config = ConfigDict(from_attributes=True)


class OrderSummary(BaseModel):
    id: int
    order_number: str
    timestamp: datetime
    customer_name: Optional[str]
    total_amount: Decimal
    payment_mode: PaymentMode
    
    @field_validator('payment_mode', mode='before')
    @classmethod
    def validate_payment_mode(cls, v):
        if v is None:
            return PaymentMode.CASH  # Default value
        if isinstance(v, str):
            # Handle string values from database
            v_lower = v.lower()
            if v_lower == 'cash':
                return PaymentMode.CASH
            elif v_lower == 'card':
                return PaymentMode.CARD
            elif v_lower == 'upi':
                return PaymentMode.UPI
            elif v_lower == 'wallet':
                return PaymentMode.WALLET
        return v
    
    model_config = ConfigDict(from_attributes=True)


class ActiveOrder(BaseModel):
    """Schema for active orders displayed in the billing page"""
    id: int
    order_number: str
    timestamp: datetime
    customer_name: Optional[str]
    food_preparation_stage: FoodPreparationStage
    payment_status: PaymentStatus
    payment_mode: PaymentMode
    total_amount: Decimal
    created_at: datetime
    
    @field_validator('food_preparation_stage', mode='before')
    @classmethod
    def validate_food_stage(cls, v):
        if v is None:
            return FoodPreparationStage.ORDERED  # Default value
        if isinstance(v, str):
            # Handle string values from database
            v_lower = v.lower()
            if v_lower == 'ordered':
                return FoodPreparationStage.ORDERED
            elif v_lower == 'preparing':
                return FoodPreparationStage.PREPARING
            elif v_lower == 'completed':
                return FoodPreparationStage.COMPLETED
        return v
    
    @field_validator('payment_status', mode='before')
    @classmethod
    def validate_payment_status(cls, v):
        if v is None:
            return PaymentStatus.PENDING  # Default value
        if isinstance(v, str):
            # Handle string values from database
            v_lower = v.lower()
            if v_lower == 'pending':
                return PaymentStatus.PENDING
            elif v_lower == 'due':
                return PaymentStatus.DUE
            elif v_lower == 'payment_done':
                return PaymentStatus.PAYMENT_DONE
            elif v_lower == 'overpaid':
                return PaymentStatus.OVERPAID
            elif v_lower == 'adjusted':
                return PaymentStatus.ADJUSTED
        return v
    
    @field_validator('payment_mode', mode='before')
    @classmethod
    def validate_payment_mode(cls, v):
        if v is None:
            return PaymentMode.CASH  # Default value
        if isinstance(v, str):
            # Handle string values from database
            v_lower = v.lower()
            if v_lower == 'cash':
                return PaymentMode.CASH
            elif v_lower == 'card':
                return PaymentMode.CARD
            elif v_lower == 'upi':
                return PaymentMode.UPI
            elif v_lower == 'wallet':
                return PaymentMode.WALLET
        return v
    
    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status"""
    food_preparation_stage: Optional[FoodPreparationStage] = None
    payment_status: Optional[PaymentStatus] = None
    payment_mode: Optional[PaymentMode] = None


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


# Expense Schemas
class ExpenseBase(BaseModel):
    date: date
    title: str
    category: str
    expense_type: ExpenseType
    amount: Decimal
    payment_mode: Optional[PaymentMode] = None
    vendor: Optional[str] = None
    notes: Optional[str] = None
    attachment: Optional[str] = None
    
    @field_validator('amount')
    @classmethod
    def validate_positive_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
    
    @field_validator('expense_type', mode='before')
    @classmethod
    def validate_expense_type(cls, v):
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == 'one-time' or v_lower == 'one_time':
                return ExpenseType.ONE_TIME
            elif v_lower == 'recurrent':
                return ExpenseType.RECURRENT
        return v
    
    @field_validator('payment_mode', mode='before')
    @classmethod
    def validate_payment_mode(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == 'cash':
                return PaymentMode.CASH
            elif v_lower == 'card':
                return PaymentMode.CARD
            elif v_lower == 'upi':
                return PaymentMode.UPI
            elif v_lower == 'wallet':
                return PaymentMode.WALLET
        return v


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    date: Optional[date] = None
    title: Optional[str] = None
    category: Optional[str] = None
    expense_type: Optional[ExpenseType] = None
    amount: Optional[Decimal] = None
    payment_mode: Optional[PaymentMode] = None
    vendor: Optional[str] = None
    notes: Optional[str] = None
    attachment: Optional[str] = None
    
    @field_validator('amount')
    @classmethod
    def validate_positive_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be positive")
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("Title cannot be empty")
        return v.strip() if v else v
    
    @field_validator('expense_type', mode='before')
    @classmethod
    def validate_expense_type(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == 'one-time' or v_lower == 'one_time':
                return ExpenseType.ONE_TIME
            elif v_lower == 'recurrent':
                return ExpenseType.RECURRENT
        return v
    
    @field_validator('payment_mode', mode='before')
    @classmethod
    def validate_payment_mode(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower == 'cash':
                return PaymentMode.CASH
            elif v_lower == 'card':
                return PaymentMode.CARD
            elif v_lower == 'upi':
                return PaymentMode.UPI
            elif v_lower == 'wallet':
                return PaymentMode.WALLET
        return v


class ExpenseOut(ExpenseBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseOut]
    total: int
    skip: int
    limit: int


class ExpenseCategorySummary(BaseModel):
    category: str
    total_amount: Decimal
    count: int


class ExpenseMonthlySummary(BaseModel):
    month: str  # Format: "YYYY-MM"
    total_amount: Decimal
    count: int


class ExpenseSummary(BaseModel):
    total_expenses: Decimal
    total_count: int
    by_category: List[ExpenseCategorySummary]
    by_month: List[ExpenseMonthlySummary]


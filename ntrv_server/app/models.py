from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, ForeignKey, 
    Integer, Numeric, String, Text
)
from sqlalchemy.orm import relationship

from app.db import Base

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now() -> datetime:
    """Get current time in IST (Indian Standard Time)"""
    return datetime.now(IST)


class OrderMode(str, PyEnum):
    IN_PERSON = "in_person"
    PHONE = "phone"
    WHATSAPP = "whatsapp"
    STREAMLIT_UI = "streamlit_ui"


class PaymentMode(str, PyEnum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    WALLET = "wallet"


class DiscountType(str, PyEnum):
    PERCENT = "percent"
    FLAT = "flat"
    NONE = "none"


class FoodPreparationStage(str, PyEnum):
    ORDERED = "ordered"
    PREPARING = "preparing"
    COMPLETED = "completed"


class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    DUE = "due"
    PAYMENT_DONE = "payment_done"
    OVERPAID = "overpaid"
    ADJUSTED = "adjusted"


class ExpenseType(str, PyEnum):
    ONE_TIME = "one-time"
    RECURRENT = "recurrent"


class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # sell price per unit
    cost = Column(Numeric(10, 2), nullable=False)   # making cost per unit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_ist_now)
    updated_at = Column(DateTime, default=get_ist_now, onupdate=get_ist_now)
    
    order_items = relationship("OrderItem", back_populates="menu_item")
    
    def __repr__(self):
        return f"<MenuItem {self.code}: {self.name}>"


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, index=True)
    timestamp = Column(DateTime, default=get_ist_now)
    customer_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    mode_of_order = Column(Enum(OrderMode), default=OrderMode.IN_PERSON)
    payment_mode = Column(Enum(PaymentMode), default=PaymentMode.CASH)
    notes = Column(Text, nullable=True)
    
    # Financial fields
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount_type = Column(Enum(DiscountType), default=DiscountType.NONE)
    discount_value = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)  # Calculated discount amount
    tax_percent = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)  # final billed amount
    
    # Cost and profit tracking
    total_making_cost = Column(Numeric(10, 2), nullable=False)
    other_costs = Column(Numeric(10, 2), default=0)  # Optional other costs
    net_amount = Column(Numeric(10, 2), nullable=False)  # total_amount - total_making_cost
    total_profit = Column(Numeric(10, 2), nullable=False)  # net_amount - other_costs
    
    # Soft delete fields
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Order management fields
    food_preparation_stage = Column(String(20), default="ordered")
    payment_status = Column(String(20), default="pending")
    payment_completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=get_ist_now)
    
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order {self.order_number}: {self.total_amount}>"


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    
    # Denormalized fields for historical record
    item_name = Column(String(100), nullable=False)
    qty = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)  # MRP (for reference)
    unit_sold_price = Column(Numeric(10, 2), nullable=True)  # Actual sold price (optional, defaults to unit_price)
    line_total = Column(Numeric(10, 2), nullable=False)  # qty * unit_sold_price (or unit_price if unit_sold_price is None)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    line_cost = Column(Numeric(10, 2), nullable=False)  # qty * unit_cost
    
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem {self.item_name}: {self.qty} x {self.unit_price}>"


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=True, index=True)
    balance = Column(Numeric(10, 2), default=Decimal('0'), nullable=False)  # Positive = credit, Negative = owes
    created_at = Column(DateTime, default=get_ist_now)
    updated_at = Column(DateTime, default=get_ist_now, onupdate=get_ist_now)
    
    def __repr__(self):
        return f"<Customer {self.name}: Balance ₹{self.balance}>"


# Expense Categories - constants for recommended categories
EXPENSE_CATEGORIES = [
    "Raw Materials",
    "Packaging",
    "Utilities",
    "Staff Salary",
    "Logistics",
    "Marketing",
    "Rent",
    "Maintenance",
    "Other"
]


class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    expense_type = Column(String(20), nullable=False)  # "one-time" | "recurrent"
    amount = Column(Numeric(12, 2), nullable=False)
    payment_mode = Column(String(30), nullable=True)  # "cash", "card", "upi", "wallet"
    vendor = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    attachment = Column(String(512), nullable=True)  # optional path to upload
    created_at = Column(DateTime, default=get_ist_now)
    
    def __repr__(self):
        return f"<Expense {self.title}: ₹{self.amount} on {self.date}>"


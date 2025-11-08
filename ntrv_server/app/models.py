from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, 
    Integer, Numeric, String, Text
)
from sqlalchemy.orm import relationship

from app.db import Base


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


class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # sell price per unit
    cost = Column(Numeric(10, 2), nullable=False)   # making cost per unit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order_items = relationship("OrderItem", back_populates="menu_item")
    
    def __repr__(self):
        return f"<MenuItem {self.code}: {self.name}>"


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
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
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)  # qty * unit_price
    unit_cost = Column(Numeric(10, 2), nullable=False)
    line_cost = Column(Numeric(10, 2), nullable=False)  # qty * unit_cost
    
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem {self.item_name}: {self.qty} x {self.unit_price}>"


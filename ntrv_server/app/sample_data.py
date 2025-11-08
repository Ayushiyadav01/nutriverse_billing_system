import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict

from sqlalchemy.orm import Session

from app.models import MenuItem, Order, OrderItem, OrderMode, PaymentMode, DiscountType
from app.db import SessionLocal, init_db
from app.crud import generate_order_number

# Sample menu items
SAMPLE_MENU_ITEMS = [
    {
        "code": "B001",
        "name": "Protein Smoothie Bowl",
        "category": "Breakfast",
        "price": Decimal("180.00"),
        "cost": Decimal("90.00"),
        "is_active": True
    },
    {
        "code": "B002",
        "name": "Avocado Toast",
        "category": "Breakfast",
        "price": Decimal("160.00"),
        "cost": Decimal("70.00"),
        "is_active": True
    },
    {
        "code": "L001",
        "name": "Quinoa Salad Bowl",
        "category": "Lunch",
        "price": Decimal("220.00"),
        "cost": Decimal("110.00"),
        "is_active": True
    },
    {
        "code": "L002",
        "name": "Grilled Chicken Wrap",
        "category": "Lunch",
        "price": Decimal("240.00"),
        "cost": Decimal("120.00"),
        "is_active": True
    },
    {
        "code": "D001",
        "name": "Protein Shake",
        "category": "Drinks",
        "price": Decimal("150.00"),
        "cost": Decimal("60.00"),
        "is_active": True
    },
    {
        "code": "D002",
        "name": "Green Detox Juice",
        "category": "Drinks",
        "price": Decimal("120.00"),
        "cost": Decimal("40.00"),
        "is_active": True
    }
]

# Sample customer names
SAMPLE_CUSTOMER_NAMES = [
    "John Smith", "Jane Doe", "Alex Johnson", "Sam Wilson", 
    "Maria Garcia", "Raj Patel", "Emma Thompson", "Liu Wei"
]

# Sample phone numbers
SAMPLE_PHONE_NUMBERS = [
    "9876543210", "8765432109", "7654321098", "6543210987",
    "9988776655", "8877665544", "7766554433", "6655443322"
]

def create_sample_menu_items(db: Session) -> List[MenuItem]:
    """Create sample menu items in the database"""
    menu_items = []
    
    for item_data in SAMPLE_MENU_ITEMS:
        db_item = MenuItem(
            code=item_data["code"],
            name=item_data["name"],
            category=item_data["category"],
            price=item_data["price"],
            cost=item_data["cost"],
            is_active=item_data["is_active"]
        )
        db.add(db_item)
        menu_items.append(db_item)
    
    db.commit()
    for item in menu_items:
        db.refresh(item)
    
    return menu_items

def create_sample_orders(db: Session, menu_items: List[MenuItem], num_orders: int = 8) -> List[Order]:
    """Create sample orders in the database"""
    orders = []
    
    # Start date for sample orders (30 days ago)
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(num_orders):
        # Generate random order data
        order_timestamp = start_date + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(8, 20),
            minutes=random.randint(0, 59)
        )
        
        customer_index = random.randint(0, len(SAMPLE_CUSTOMER_NAMES) - 1)
        customer_name = SAMPLE_CUSTOMER_NAMES[customer_index]
        phone = SAMPLE_PHONE_NUMBERS[customer_index]
        
        mode_of_order = random.choice(list(OrderMode))
        payment_mode = random.choice(list(PaymentMode))
        
        # Randomly decide if there's a discount
        has_discount = random.random() < 0.3  # 30% chance of having a discount
        discount_type = DiscountType.NONE
        discount_value = Decimal('0')
        
        if has_discount:
            discount_type = random.choice([DiscountType.FLAT, DiscountType.PERCENT])
            if discount_type == DiscountType.FLAT:
                discount_value = Decimal(str(random.randint(10, 50)))
            else:  # PERCENT
                discount_value = Decimal(str(random.randint(5, 20)))
        
        tax_percent = Decimal('5.0')  # 5% tax
        
        # Generate order items (1 to 4 items per order)
        num_items = random.randint(1, 4)
        selected_items = random.sample(menu_items, num_items)
        
        order_items = []
        subtotal = Decimal('0')
        total_making_cost = Decimal('0')
        
        for menu_item in selected_items:
            qty = random.randint(1, 3)
            unit_price = menu_item.price
            unit_cost = menu_item.cost
            
            line_total = unit_price * qty
            line_cost = unit_cost * qty
            
            subtotal += line_total
            total_making_cost += line_cost
            
            order_items.append({
                "menu_item": menu_item,
                "item_name": menu_item.name,
                "qty": qty,
                "unit_price": unit_price,
                "line_total": line_total,
                "unit_cost": unit_cost,
                "line_cost": line_cost
            })
        
        # Calculate discount amount
        discount_amount = Decimal('0')
        if discount_type == DiscountType.FLAT:
            discount_amount = min(discount_value, subtotal)
        elif discount_type == DiscountType.PERCENT:
            discount_amount = (subtotal * discount_value / 100).quantize(Decimal('0.01'))
        
        # Calculate tax
        taxable_amount = subtotal - discount_amount
        tax_amount = (taxable_amount * tax_percent / 100).quantize(Decimal('0.01'))
        
        # Calculate final totals
        total_amount = taxable_amount + tax_amount
        other_costs = Decimal('0')
        net_amount = total_amount - total_making_cost
        total_profit = net_amount - other_costs
        
        # Generate order number
        order_number = generate_order_number(db, "NV")
        
        # Create order
        db_order = Order(
            order_number=order_number,
            timestamp=order_timestamp,
            customer_name=customer_name,
            phone=phone,
            mode_of_order=mode_of_order,
            payment_mode=payment_mode,
            notes=f"Sample order {i+1}",
            subtotal=subtotal,
            discount_type=discount_type,
            discount_value=discount_value,
            discount_amount=discount_amount,
            tax_percent=tax_percent,
            tax_amount=tax_amount,
            total_amount=total_amount,
            total_making_cost=total_making_cost,
            other_costs=other_costs,
            net_amount=net_amount,
            total_profit=total_profit
        )
        
        db.add(db_order)
        db.flush()  # To get the order.id
        
        # Create order items
        for item_data in order_items:
            db_order_item = OrderItem(
                order_id=db_order.id,
                menu_item_id=item_data["menu_item"].id,
                item_name=item_data["item_name"],
                qty=item_data["qty"],
                unit_price=item_data["unit_price"],
                line_total=item_data["line_total"],
                unit_cost=item_data["unit_cost"],
                line_cost=item_data["line_cost"]
            )
            db.add(db_order_item)
        
        orders.append(db_order)
    
    db.commit()
    for order in orders:
        db.refresh(order)
    
    return orders

def create_all_sample_data():
    """Create all sample data in the database"""
    # Initialize database
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Create sample menu items
        menu_items = create_sample_menu_items(db)
        print(f"Created {len(menu_items)} sample menu items")
        
        # Create sample orders
        orders = create_sample_orders(db, menu_items)
        print(f"Created {len(orders)} sample orders")
        
        return True
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    create_all_sample_data()


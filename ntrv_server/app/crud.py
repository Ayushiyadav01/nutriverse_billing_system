from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy import func, extract, text, or_, and_
from sqlalchemy.orm import Session

from app.models import MenuItem, Order, OrderItem, OrderMode, PaymentMode, DiscountType, FoodPreparationStage, PaymentStatus, Expense, ExpenseType, Customer, get_ist_now
from app.schemas import MenuItemCreate, MenuItemUpdate, OrderCreate, OrderUpdate, DiscountInfo, ExpenseCreate, ExpenseUpdate, CustomerCreate, CustomerUpdate
from app.config import settings
from decimal import ROUND_HALF_UP

def quantize_amount(amount: Decimal) -> Decimal:
    """Quantize amount to 2 decimal places"""
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# Menu Item CRUD operations
def get_menu_item(db: Session, item_id: int) -> Optional[MenuItem]:
    return db.query(MenuItem).filter(MenuItem.id == item_id).first()


def get_menu_item_by_code(db: Session, code: str) -> Optional[MenuItem]:
    return db.query(MenuItem).filter(MenuItem.code == code.upper()).first()


def get_menu_items(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = False
) -> List[MenuItem]:
    query = db.query(MenuItem)
    if active_only:
        query = query.filter(MenuItem.is_active == True)
    return query.order_by(MenuItem.category, MenuItem.name).offset(skip).limit(limit).all()


def create_menu_item(db: Session, item: MenuItemCreate) -> MenuItem:
    db_item = MenuItem(
        code=item.code.upper(),
        name=item.name,
        category=item.category,
        price=item.price,
        cost=item.cost,
        is_active=item.is_active
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_menu_item(
    db: Session, 
    item_id: int, 
    item_update: MenuItemUpdate
) -> Optional[MenuItem]:
    db_item = get_menu_item(db, item_id)
    if not db_item:
        return None
    
    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_menu_item(db: Session, item_id: int) -> Optional[MenuItem]:
    db_item = get_menu_item(db, item_id)
    if not db_item:
        return None
    
    # Soft delete - just mark as inactive
    db_item.is_active = False
    db.commit()
    db.refresh(db_item)
    return db_item


# Order CRUD operations
def get_order(db: Session, order_id: int) -> Optional[Order]:
    return db.query(Order).filter(
        Order.id == order_id,
        Order.is_deleted.is_(False)
    ).first()


def get_order_by_number(db: Session, order_number: str) -> Optional[Order]:
    return db.query(Order).filter(
        Order.order_number == order_number,
        Order.is_deleted.is_(False)
    ).first()


def get_orders(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    mode_of_order: Optional[OrderMode] = None,
    payment_mode: Optional[PaymentMode] = None,
    time_of_day: Optional[str] = None,
    item_id: Optional[int] = None
) -> List[Order]:
    query = db.query(Order).filter(Order.is_deleted.is_(False))
    
    # Apply filters
    if date_from:
        query = query.filter(Order.timestamp >= date_from)
    if date_to:
        query = query.filter(Order.timestamp <= date_to)
    if mode_of_order:
        query = query.filter(Order.mode_of_order == mode_of_order)
    if payment_mode:
        query = query.filter(Order.payment_mode == payment_mode)
    
    # Time of day filter
    if time_of_day:
        if time_of_day == "morning":
            query = query.filter(extract('hour', Order.timestamp).between(6, 11))
        elif time_of_day == "afternoon":
            query = query.filter(extract('hour', Order.timestamp).between(12, 16))
        elif time_of_day == "evening":
            query = query.filter(extract('hour', Order.timestamp).between(17, 20))
        elif time_of_day == "night":
            query = query.filter((extract('hour', Order.timestamp) >= 21) | 
                                 (extract('hour', Order.timestamp) < 6))
    
    # Filter by item_id
    if item_id:
        query = query.join(Order.items).filter(OrderItem.menu_item_id == item_id)
    
    # Order by timestamp descending (newest first)
    query = query.order_by(Order.timestamp.desc())
    
    return query.offset(skip).limit(limit).all()


def generate_order_number(db: Session, prefix: str = "NV") -> str:
    """Generate a unique order number with format: PREFIX-YYYYMMDD-NNNN"""
    today = date.today().strftime("%Y%m%d")
    
    # Get the last order number for today
    last_order = db.query(Order).filter(
        Order.order_number.like(f"{prefix}-{today}-%")
    ).order_by(Order.order_number.desc()).first()
    
    if last_order:
        # Extract the sequence number and increment
        seq_num = int(last_order.order_number.split('-')[-1]) + 1
    else:
        # First order of the day
        seq_num = 1
    
    return f"{prefix}-{today}-{seq_num:04d}"


def create_order(
    db: Session, 
    order_data: OrderCreate, 
    order_number_prefix: str = "NV"
) -> Order:
    # Process items first to calculate totals
    order_items = []
    subtotal = Decimal('0')
    total_making_cost = Decimal('0')
    
    for item_data in order_data.items:
        # Get menu item either by ID or code
        menu_item = None
        if item_data.menu_item_id:
            menu_item = get_menu_item(db, item_data.menu_item_id)
        elif item_data.menu_item_code:
            menu_item = get_menu_item_by_code(db, item_data.menu_item_code)
        
        if not menu_item:
            raise ValueError(f"Menu item not found: ID={item_data.menu_item_id}, Code={item_data.menu_item_code}")
        
        # Calculate line totals
        qty = item_data.qty
        unit_price = menu_item.price  # MRP (for reference)
        unit_sold_price = item_data.sold_price if item_data.sold_price is not None else unit_price  # Use sold_price if provided, else MRP
        unit_cost = menu_item.cost
        line_total = unit_sold_price * qty  # Use sold price for calculations
        line_cost = unit_cost * qty
        
        # Add to running totals
        subtotal += line_total
        total_making_cost += line_cost
        
        # Create order item
        order_item_dict = {
            "menu_item_id": menu_item.id,
            "item_name": menu_item.name,
            "qty": qty,
            "unit_price": unit_price,  # Store MRP for reference
            "line_total": line_total,
            "unit_cost": unit_cost,
            "line_cost": line_cost
        }
        # Only add unit_sold_price if it differs from MRP (for backward compatibility)
        if unit_sold_price != unit_price:
            order_item_dict["unit_sold_price"] = unit_sold_price
        
        order_items.append(order_item_dict)
    
    # Calculate discount
    discount_type = order_data.discount.type
    discount_value = order_data.discount.value
    discount_amount = Decimal('0')
    
    if discount_type == DiscountType.FLAT:
        discount_amount = min(discount_value, subtotal)  # Can't discount more than subtotal
    elif discount_type == DiscountType.PERCENT:
        discount_amount = (subtotal * discount_value / 100).quantize(Decimal('0.01'))
    
    # Calculate tax
    taxable_amount = subtotal - discount_amount
    tax_percent = order_data.tax_percent
    tax_amount = (taxable_amount * tax_percent / 100).quantize(Decimal('0.01'))
    
    # Calculate final totals
    total_amount = taxable_amount + tax_amount
    other_costs = order_data.other_costs
    net_amount = total_amount - total_making_cost
    total_profit = net_amount - other_costs
    
    # Generate unique order number
    order_number = generate_order_number(db, order_number_prefix)
    
    # Create order
    db_order = Order(
        order_number=order_number,
        customer_name=order_data.customer_name,
        phone=order_data.phone,
        mode_of_order=order_data.mode_of_order,
        payment_mode=order_data.payment_mode,
        notes=order_data.notes,
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
        total_profit=total_profit,
        food_preparation_stage=order_data.food_preparation_stage.value if hasattr(order_data.food_preparation_stage, 'value') else str(order_data.food_preparation_stage).lower(),
        payment_status=order_data.payment_status.value if hasattr(order_data.payment_status, 'value') else str(order_data.payment_status).lower()
    )
    
    db.add(db_order)
    db.flush()  # To get the order.id
    
    # Create order items
    for item_data in order_items:
        db_order_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_order_item)
    
    # Handle customer balance update if customer_name is provided
    if order_data.customer_name:
        customer = get_or_create_customer(db, order_data.customer_name, order_data.phone)
        if customer:
            # Determine customer_paid_amount
            if order_data.customer_paid_amount is not None:
                # Use provided customer_paid_amount
                customer_paid = order_data.customer_paid_amount
            else:
                # Infer from payment_status
                payment_status_str = order_data.payment_status.value if hasattr(order_data.payment_status, 'value') else str(order_data.payment_status).lower()
                if payment_status_str == "payment_done":
                    # Assume full payment
                    customer_paid = total_amount
                elif payment_status_str in ["due", "pending"]:
                    # Assume no payment
                    customer_paid = Decimal('0')
                else:
                    # For other statuses, assume no payment
                    customer_paid = Decimal('0')
            
            # Calculate new balance: old_balance + customer_paid_amount - total_bill_amount
            new_balance = customer.balance + customer_paid - total_amount
            customer.balance = quantize_amount(new_balance)
            customer.updated_at = get_ist_now()
            db.add(customer)
    
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order(
    db: Session, 
    order_id: int, 
    order_update: OrderUpdate
) -> Optional[Order]:
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    update_data = order_update.dict(exclude_unset=True)
    
    # Convert enum values to strings for food_preparation_stage and payment_status
    if 'food_preparation_stage' in update_data:
        val = update_data['food_preparation_stage']
        update_data['food_preparation_stage'] = val.value if hasattr(val, 'value') else str(val).lower()
    
    if 'payment_status' in update_data:
        val = update_data['payment_status']
        payment_status_str = val.value if hasattr(val, 'value') else str(val).lower()
        current_status = db_order.payment_status or ""
        
        # If payment_status is being updated to PAYMENT_DONE, set payment_completed_at
        if payment_status_str == "payment_done" and current_status != "payment_done":
            update_data['payment_completed_at'] = get_ist_now()
        elif payment_status_str != "payment_done":
            # If changing from PAYMENT_DONE to something else, clear payment_completed_at
            update_data['payment_completed_at'] = None
        update_data['payment_status'] = payment_status_str
    
    if 'payment_mode' in update_data:
        val = update_data['payment_mode']
        update_data['payment_mode'] = val.value if hasattr(val, 'value') else str(val).lower()
    
    for key, value in update_data.items():
        setattr(db_order, key, value)
    
    db.commit()
    db.refresh(db_order)
    return db_order


def soft_delete_order(db: Session, order_id: int) -> Optional[Order]:
    """Soft delete an order by setting is_deleted=True and deleted_at timestamp"""
    # Get order without checking is_deleted to allow deleting already deleted orders
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        return None
    
    # Check if already deleted
    if db_order.is_deleted:
        return None  # Already deleted
    
    # Soft delete
    db_order.is_deleted = True
    db_order.deleted_at = get_ist_now()
    
    db.commit()
    db.refresh(db_order)
    return db_order


def soft_delete_order_by_number(db: Session, order_number: str) -> Optional[Order]:
    """Soft delete an order by order_number"""
    # Get order without checking is_deleted to allow deleting already deleted orders
    db_order = db.query(Order).filter(Order.order_number == order_number).first()
    if not db_order:
        return None
    
    # Check if already deleted
    if db_order.is_deleted:
        return None  # Already deleted
    
    # Soft delete
    db_order.is_deleted = True
    db_order.deleted_at = get_ist_now()
    
    db.commit()
    db.refresh(db_order)
    return db_order


def get_active_orders(db: Session) -> List[Order]:
    """Get active orders (Ordered or Preparing, not Payment Done, not Due)"""
    return db.query(Order).filter(
        Order.is_deleted.is_(False),
        Order.food_preparation_stage.in_(["ordered", "preparing"]),
        Order.payment_status.notin_(["payment_done", "due"]),
        # Also filter out NULL values (for orders created before migration)
        Order.food_preparation_stage.isnot(None),
        Order.payment_status.isnot(None)
    ).order_by(Order.created_at.desc()).all()


def get_due_payments(db: Session) -> List[Order]:
    """Get orders with pending or due payments"""
    return db.query(Order).filter(
        Order.is_deleted.is_(False),
        Order.payment_status.in_(["pending", "due"]),
        # Also filter out NULL values (for orders created before migration)
        Order.payment_status.isnot(None)
    ).order_by(Order.created_at.desc()).all()


def update_order_status(
    db: Session,
    order_id: int,
    food_preparation_stage: Optional[FoodPreparationStage] = None,
    payment_status: Optional[PaymentStatus] = None,
    payment_mode: Optional[PaymentMode] = None
) -> Optional[Order]:
    """Update order status (preparation stage, payment status, and/or payment mode)"""
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    if food_preparation_stage is not None:
        # Convert enum to string value
        db_order.food_preparation_stage = food_preparation_stage.value if hasattr(food_preparation_stage, 'value') else str(food_preparation_stage).lower()
    
    if payment_status is not None:
        # Convert enum to string value
        payment_status_str = payment_status.value if hasattr(payment_status, 'value') else str(payment_status).lower()
        current_status = db_order.payment_status or ""
        
        # If payment_status is being updated to PAYMENT_DONE, set payment_completed_at
        if payment_status_str == "payment_done" and current_status != "payment_done":
            db_order.payment_completed_at = get_ist_now()
        elif payment_status_str != "payment_done":
            # If changing from PAYMENT_DONE to something else, clear payment_completed_at
            db_order.payment_completed_at = None
        db_order.payment_status = payment_status_str
    
    if payment_mode is not None:
        # Convert enum to string value
        db_order.payment_mode = payment_mode.value if hasattr(payment_mode, 'value') else str(payment_mode).lower()
    
    db.commit()
    db.refresh(db_order)
    return db_order


# Analytics functions
def get_analytics_summary(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict:
    query = db.query(
        func.count(Order.id).label("total_orders"),
        func.sum(Order.total_amount).label("total_sales"),
        func.sum(Order.total_making_cost).label("total_making_cost"),
        func.sum(Order.total_profit).label("total_profit")
    ).filter(Order.is_deleted.is_(False))
    
    if date_from:
        query = query.filter(Order.timestamp >= date_from)
    if date_to:
        query = query.filter(Order.timestamp <= date_to)
    
    result = query.first()
    
    # Calculate average order value
    total_orders = result.total_orders or 0
    total_sales = result.total_sales or Decimal('0')
    avg_order_value = Decimal('0')
    if total_orders > 0:
        avg_order_value = (total_sales / total_orders).quantize(Decimal('0.01'))
    
    return {
        "total_orders": total_orders,
        "total_sales": result.total_sales or Decimal('0'),
        "total_making_cost": result.total_making_cost or Decimal('0'),
        "total_profit": result.total_profit or Decimal('0'),
        "average_order_value": avg_order_value
    }


def get_top_selling_items(
    db: Session,
    limit: int = 10,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[Dict]:
    query = db.query(
        OrderItem.item_name,
        MenuItem.category,
        func.sum(OrderItem.qty).label("total_qty"),
        func.sum(OrderItem.line_total).label("total_sales")
    ).join(
        MenuItem, MenuItem.id == OrderItem.menu_item_id
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.is_deleted == False
    ).group_by(
        OrderItem.item_name, MenuItem.category
    )
    
    if date_from:
        query = query.filter(Order.timestamp >= date_from)
    if date_to:
        query = query.filter(Order.timestamp <= date_to)
    
    query = query.order_by(func.sum(OrderItem.qty).desc())
    
    results = query.limit(limit).all()
    return [
        {
            "item_name": item.item_name,
            "category": item.category,
            "total_qty": item.total_qty,
            "total_sales": item.total_sales
        }
        for item in results
    ]


def get_sales_by_time_unit(
    db: Session,
    time_unit: str = "day",
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[Dict]:
    """Get sales aggregated by time unit (hour, day, week, month)"""
    
    # Check if we're using SQLite
    is_sqlite = "sqlite" in settings.DATABASE_URL.lower()
    
    if time_unit == "hour":
        if is_sqlite:
            # SQLite: use strftime for hour formatting
            time_extract = func.strftime('%H', Order.timestamp)
            time_format = time_extract.label("time_unit")
        else:
            # PostgreSQL: use to_char
            time_extract = extract('hour', Order.timestamp)
            time_format = func.to_char(Order.timestamp, 'HH24:00').label("time_unit")
    elif time_unit == "day":
        if is_sqlite:
            # SQLite: use strftime for date formatting
            time_extract = func.strftime('%Y-%m-%d', Order.timestamp)
            time_format = time_extract.label("time_unit")
        else:
            # PostgreSQL: use date and to_char
            time_extract = func.date(Order.timestamp)
            time_format = func.to_char(Order.timestamp, 'YYYY-MM-DD').label("time_unit")
    elif time_unit == "week":
        if is_sqlite:
            # SQLite: use strftime for week formatting
            time_extract = func.strftime('%Y-W%W', Order.timestamp)
            time_format = time_extract.label("time_unit")
        else:
            # PostgreSQL: use extract and to_char
            time_extract = extract('week', Order.timestamp)
            time_format = func.concat(
                func.to_char(Order.timestamp, 'YYYY-'),
                text("'Week '"),
                func.to_char(Order.timestamp, 'WW')
            ).label("time_unit")
    elif time_unit == "month":
        if is_sqlite:
            # SQLite: use strftime for month formatting
            time_extract = func.strftime('%Y-%m', Order.timestamp)
            time_format = time_extract.label("time_unit")
        else:
            # PostgreSQL: use extract and to_char
            time_extract = extract('month', Order.timestamp)
            time_format = func.to_char(Order.timestamp, 'YYYY-MM').label("time_unit")
    else:
        raise ValueError(f"Invalid time unit: {time_unit}")
    
    query = db.query(
        time_format,
        func.sum(Order.total_amount).label("sales"),
        func.count(Order.id).label("orders_count")
    ).filter(Order.is_deleted.is_(False))
    
    # Apply filters
    if date_from:
        query = query.filter(Order.timestamp >= date_from)
    if date_to:
        query = query.filter(Order.timestamp <= date_to)
    
    # Group by and order by - use time_extract (the base expression) for both
    query = query.group_by(time_extract)
    query = query.order_by(time_extract)
    
    results = query.all()
    
    # Format results based on time unit
    formatted_results = []
    for item in results:
        time_unit_str = str(item.time_unit)
        
        # For SQLite hour queries, format as HH:00
        if time_unit == "hour" and is_sqlite:
            try:
                # item.time_unit is a string like "08" or "23"
                hour_str = str(item.time_unit).zfill(2)  # Ensure 2 digits
                time_unit_str = f"{hour_str}:00"
            except (ValueError, TypeError):
                time_unit_str = str(item.time_unit)
        
        formatted_results.append({
            "time_unit": time_unit_str,
            "sales": item.sales or Decimal('0'),
            "orders_count": item.orders_count or 0
        })
    
    return formatted_results


def get_customer_details(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[Dict]:
    """Get unique customers with their total purchase amounts"""
    query = db.query(
        Order.customer_name,
        Order.phone,
        func.sum(Order.total_amount).label("total_purchased"),
        func.count(Order.id).label("total_orders")
    ).filter(
        Order.customer_name.isnot(None),
        Order.customer_name != "",
        Order.is_deleted.is_(False)
    ).group_by(
        Order.customer_name, Order.phone
    )
    
    if date_from:
        query = query.filter(Order.timestamp >= date_from)
    if date_to:
        query = query.filter(Order.timestamp <= date_to)
    
    query = query.order_by(func.sum(Order.total_amount).desc())
    
    results = query.all()
    return [
        {
            "customer_name": item.customer_name,
            "phone": item.phone or "N/A",
            "total_purchased": item.total_purchased or Decimal('0'),
            "total_orders": item.total_orders or 0
        }
        for item in results
    ]


def get_customer_autocomplete(db: Session, search_query: Optional[str] = None) -> List[Dict]:
    """Get unique customer names and phones for autocomplete suggestions"""
    query = db.query(
        Order.customer_name,
        Order.phone
    ).filter(
        Order.customer_name.isnot(None),
        Order.customer_name != "",
        Order.is_deleted.is_(False)
    ).distinct()
    
    # Filter by search query if provided (case-insensitive)
    if search_query:
        search_lower = search_query.lower()
        # Use func.lower() for better database compatibility
        # Build filter conditions
        filters = [
            func.lower(Order.customer_name).like(f"%{search_lower}%")
        ]
        # Add phone filter only if phone is not None
        filters.append(
            and_(
                Order.phone.isnot(None),
                func.lower(Order.phone).like(f"%{search_lower}%")
            )
        )
        query = query.filter(or_(*filters))
    
    query = query.order_by(Order.customer_name).limit(50)  # Limit to 50 suggestions
    
    results = query.all()
    return [
        {
            "customer_name": item.customer_name,
            "phone": item.phone or ""
        }
        for item in results
    ]


# Expense CRUD operations
def create_expense(db: Session, expense: ExpenseCreate) -> Expense:
    """Create a new expense"""
    db_expense = Expense(
        date=expense.date,
        title=expense.title,
        category=expense.category,
        expense_type=expense.expense_type.value if isinstance(expense.expense_type, ExpenseType) else expense.expense_type,
        amount=expense.amount,
        payment_mode=expense.payment_mode.value if expense.payment_mode and isinstance(expense.payment_mode, PaymentMode) else expense.payment_mode,
        vendor=expense.vendor,
        notes=expense.notes,
        attachment=expense.attachment
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def get_expense(db: Session, expense_id: int) -> Optional[Expense]:
    """Get a single expense by ID"""
    return db.query(Expense).filter(Expense.id == expense_id).first()


def list_expenses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = None,
    expense_type: Optional[str] = None,
    payment_mode: Optional[str] = None
) -> Tuple[List[Expense], int]:
    """List expenses with filters"""
    query = db.query(Expense)
    
    # Apply filters
    if date_from:
        query = query.filter(Expense.date >= date_from)
    if date_to:
        query = query.filter(Expense.date <= date_to)
    if category:
        query = query.filter(Expense.category == category)
    if expense_type:
        query = query.filter(Expense.expense_type == expense_type)
    if payment_mode:
        query = query.filter(Expense.payment_mode == payment_mode)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering
    expenses = query.order_by(Expense.date.desc(), Expense.created_at.desc()).offset(skip).limit(limit).all()
    
    return expenses, total


def update_expense(db: Session, expense_id: int, expense_update: ExpenseUpdate) -> Optional[Expense]:
    """Update an expense"""
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        return None
    
    update_data = expense_update.dict(exclude_unset=True)
    
    # Convert enum values to strings for storage
    if 'expense_type' in update_data and update_data['expense_type']:
        if isinstance(update_data['expense_type'], ExpenseType):
            update_data['expense_type'] = update_data['expense_type'].value
    if 'payment_mode' in update_data and update_data['payment_mode']:
        if isinstance(update_data['payment_mode'], PaymentMode):
            update_data['payment_mode'] = update_data['payment_mode'].value
    
    for key, value in update_data.items():
        setattr(db_expense, key, value)
    
    db.commit()
    db.refresh(db_expense)
    return db_expense


def delete_expense(db: Session, expense_id: int) -> Optional[Expense]:
    """Delete an expense (hard delete)"""
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        return None
    
    db.delete(db_expense)
    db.commit()
    return db_expense


def get_expense_summary(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Dict:
    """Get expense summary with totals and breakdowns"""
    query = db.query(Expense)
    
    # Apply date filters
    if date_from:
        query = query.filter(Expense.date >= date_from)
    if date_to:
        query = query.filter(Expense.date <= date_to)
    
    # Total expenses
    total_expenses = query.with_entities(func.sum(Expense.amount)).scalar() or Decimal('0')
    total_count = query.count()
    
    # Group by category - create a fresh query
    category_query = db.query(Expense)
    if date_from:
        category_query = category_query.filter(Expense.date >= date_from)
    if date_to:
        category_query = category_query.filter(Expense.date <= date_to)
    
    category_query = category_query.with_entities(
        Expense.category,
        func.sum(Expense.amount).label('total_amount'),
        func.count(Expense.id).label('count')
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc())
    
    by_category = [
        {
            "category": row.category,
            "total_amount": Decimal(str(row.total_amount)) if row.total_amount is not None else Decimal('0'),
            "count": row.count
        }
        for row in category_query.all()
    ]
    
    # Group by month - create a fresh query
    month_query = db.query(Expense)
    if date_from:
        month_query = month_query.filter(Expense.date >= date_from)
    if date_to:
        month_query = month_query.filter(Expense.date <= date_to)
    
    # For SQLite, use strftime; for PostgreSQL, use to_char
    try:
        db_type = str(db.bind.url).split(':')[0] if hasattr(db.bind, 'url') else 'sqlite'
    except:
        db_type = 'sqlite'
    
    if 'sqlite' in db_type.lower():
        month_format = func.strftime('%Y-%m', Expense.date)
    else:
        # PostgreSQL
        month_format = func.to_char(Expense.date, 'YYYY-MM')
    
    month_query = month_query.with_entities(
        month_format.label('month'),
        func.sum(Expense.amount).label('total_amount'),
        func.count(Expense.id).label('count')
    ).group_by(month_format).order_by(month_format)
    
    by_month = [
        {
            "month": str(row.month),
            "total_amount": Decimal(str(row.total_amount)) if row.total_amount is not None else Decimal('0'),
            "count": row.count
        }
        for row in month_query.all()
    ]
    
    return {
        "total_expenses": Decimal(str(total_expenses)) if total_expenses is not None else Decimal('0'),
        "total_count": total_count,
        "by_category": by_category,
        "by_month": by_month
    }


# Customer CRUD operations
def get_customer_by_name_and_phone(db: Session, name: str, phone: Optional[str] = None) -> Optional[Customer]:
    """Get customer by name and optionally phone"""
    if phone:
        return db.query(Customer).filter(
            Customer.name == name,
            Customer.phone == phone
        ).first()
    else:
        return db.query(Customer).filter(Customer.name == name).first()


def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    """Get customer by ID"""
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_or_create_customer(db: Session, name: str, phone: Optional[str] = None) -> Customer:
    """Get existing customer or create a new one"""
    customer = get_customer_by_name_and_phone(db, name, phone)
    if not customer:
        customer = Customer(name=name, phone=phone, balance=Decimal('0'))
        db.add(customer)
        db.flush()
    return customer


def update_customer_balance(db: Session, customer_id: int, new_balance: Decimal) -> Optional[Customer]:
    """Update customer balance manually"""
    customer = get_customer(db, customer_id)
    if not customer:
        return None
    customer.balance = quantize_amount(new_balance)
    customer.updated_at = get_ist_now()
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_all_customers(db: Session, skip: int = 0, limit: int = 1000) -> List[Customer]:
    """Get all customers with their balances"""
    return db.query(Customer).order_by(Customer.name).offset(skip).limit(limit).all()


def add_customer_payment(db: Session, customer_id: int, payment_amount: Decimal, notes: Optional[str] = None) -> Optional[Customer]:
    """Add payment to customer balance (increases balance)"""
    customer = get_customer(db, customer_id)
    if not customer:
        return None
    # Add payment amount to balance (positive amount increases balance/credit)
    customer.balance = quantize_amount(customer.balance + payment_amount)
    customer.updated_at = get_ist_now()
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def calculate_balance_from_orders(db: Session, name: str, phone: Optional[str] = None) -> Decimal:
    """Calculate customer balance from all historical orders.
    For orders without customer_paid_amount, infer from payment_status."""
    query = db.query(Order).filter(
        Order.customer_name == name,
        Order.is_deleted.is_(False)
    )
    
    if phone:
        query = query.filter(Order.phone == phone)
    else:
        # If no phone provided, match orders with no phone or empty phone
        query = query.filter(
            or_(
                Order.phone.is_(None),
                Order.phone == ""
            )
        )
    
    orders = query.all()
    balance = Decimal('0')
    
    for order in orders:
        # Try to get customer_paid_amount from order notes or other fields
        # For now, we'll infer from payment_status
        payment_status = (order.payment_status or "").lower()
        
        if payment_status == "payment_done":
            # Assume full payment
            customer_paid = order.total_amount
        elif payment_status in ["due", "pending"]:
            # Assume no payment
            customer_paid = Decimal('0')
        else:
            # Default: assume no payment
            customer_paid = Decimal('0')
        
        # Calculate: balance += customer_paid - total_amount
        balance = balance + customer_paid - order.total_amount
    
    return quantize_amount(balance)


def get_customer_balance_by_name(db: Session, name: str, phone: Optional[str] = None) -> Optional[Decimal]:
    """Get customer balance by name and optionally phone.
    If customer exists in customers table, return their balance.
    Otherwise, calculate balance from historical orders and create customer record."""
    customer = get_customer_by_name_and_phone(db, name, phone)
    if customer:
        return customer.balance
    
    # Customer doesn't exist in customers table, calculate balance from historical orders
    balance = calculate_balance_from_orders(db, name, phone)
    
    # Create customer record with calculated balance
    customer = get_or_create_customer(db, name, phone)
    customer.balance = balance
    customer.updated_at = get_ist_now()
    db.add(customer)
    db.commit()  # Commit to ensure customer is saved
    db.refresh(customer)
    
    return customer.balance


from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy import func, extract, text, or_, and_
from sqlalchemy.orm import Session

from app.models import MenuItem, Order, OrderItem, OrderMode, PaymentMode, DiscountType
from app.schemas import MenuItemCreate, MenuItemUpdate, OrderCreate, OrderUpdate, DiscountInfo
from app.config import settings


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
        unit_price = menu_item.price
        unit_cost = menu_item.cost
        line_total = unit_price * qty
        line_cost = unit_cost * qty
        
        # Add to running totals
        subtotal += line_total
        total_making_cost += line_cost
        
        # Create order item
        order_items.append({
            "menu_item_id": menu_item.id,
            "item_name": menu_item.name,
            "qty": qty,
            "unit_price": unit_price,
            "line_total": line_total,
            "unit_cost": unit_cost,
            "line_cost": line_cost
        })
    
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
        total_profit=total_profit
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
    db_order.deleted_at = datetime.utcnow()
    
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
    db_order.deleted_at = datetime.utcnow()
    
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


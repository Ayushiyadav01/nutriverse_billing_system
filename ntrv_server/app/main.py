from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
import os

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, models, schemas, utils
from app.db import get_db, init_db
from app.config import settings
from app.models import FoodPreparationStage, PaymentStatus, PaymentMode

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables
@app.on_event("startup")
def startup_event():
    init_db()


# Menu Item endpoints
@app.post("/api/menu/", response_model=schemas.MenuItem, status_code=status.HTTP_201_CREATED)
def create_menu_item(item: schemas.MenuItemCreate, db: Session = Depends(get_db)):
    # Check if menu item with same code already exists
    db_item = crud.get_menu_item_by_code(db, code=item.code)
    if db_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Menu item with code {item.code} already exists"
        )
    return crud.create_menu_item(db=db, item=item)


@app.get("/api/menu/", response_model=List[schemas.MenuItem])
def read_menu_items(
    active_only: bool = False, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    items = crud.get_menu_items(db, skip=skip, limit=limit, active_only=active_only)
    return items


@app.get("/api/menu/{item_id}", response_model=schemas.MenuItem)
def read_menu_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_menu_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with ID {item_id} not found"
        )
    return db_item


@app.get("/api/menu/code/{code}", response_model=schemas.MenuItem)
def read_menu_item_by_code(code: str, db: Session = Depends(get_db)):
    db_item = crud.get_menu_item_by_code(db, code=code)
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with code {code} not found"
        )
    return db_item


@app.put("/api/menu/{item_id}", response_model=schemas.MenuItem)
def update_menu_item(
    item_id: int, 
    item_update: schemas.MenuItemUpdate, 
    db: Session = Depends(get_db)
):
    db_item = crud.update_menu_item(db, item_id=item_id, item_update=item_update)
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with ID {item_id} not found"
        )
    return db_item


@app.delete("/api/menu/{item_id}", response_model=schemas.MenuItem)
def delete_menu_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.delete_menu_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Menu item with ID {item_id} not found"
        )
    return db_item


# Order endpoints
@app.post("/api/orders/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_order(
            db=db, 
            order_data=order, 
            order_number_prefix=settings.ORDER_NUMBER_PREFIX
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/orders/active", response_model=List[schemas.ActiveOrder])
def get_active_orders(db: Session = Depends(get_db)):
    """Get active orders (Ordered or Preparing, not Payment Done, not Due)"""
    orders = crud.get_active_orders(db)
    # Convert Order objects using Pydantic schema for proper validation
    result = []
    for order in orders:
        # Handle enum values - they might be enum instances or strings from database
        food_stage = order.food_preparation_stage
        if food_stage is None:
            food_stage = "ordered"
        elif hasattr(food_stage, 'value'):
            food_stage = food_stage.value
        else:
            food_stage = str(food_stage).lower()
        
        payment_status = order.payment_status
        if payment_status is None:
            payment_status = "pending"
        elif hasattr(payment_status, 'value'):
            payment_status = payment_status.value
        else:
            payment_status = str(payment_status).lower()
        
        payment_mode = order.payment_mode
        if payment_mode is None:
            payment_mode = "cash"
        elif hasattr(payment_mode, 'value'):
            payment_mode = payment_mode.value
        else:
            payment_mode = str(payment_mode).lower()
        
        order_dict = {
            "id": order.id,
            "order_number": order.order_number,
            "timestamp": order.timestamp,
            "customer_name": order.customer_name,
            "food_preparation_stage": food_stage,
            "payment_status": payment_status,
            "payment_mode": payment_mode,
            "total_amount": order.total_amount,
            "created_at": order.created_at
        }
        result.append(order_dict)
    return result


@app.get("/api/orders/due-payments", response_model=List[schemas.ActiveOrder])
def get_due_payments(db: Session = Depends(get_db)):
    """Get orders with pending or due payments"""
    orders = crud.get_due_payments(db)
    # Convert Order objects using Pydantic schema for proper validation
    result = []
    for order in orders:
        # Handle enum values - they might be enum instances or strings from database
        food_stage = order.food_preparation_stage
        if food_stage is None:
            food_stage = "ordered"
        elif hasattr(food_stage, 'value'):
            food_stage = food_stage.value
        else:
            food_stage = str(food_stage).lower()
        
        payment_status = order.payment_status
        if payment_status is None:
            payment_status = "pending"
        elif hasattr(payment_status, 'value'):
            payment_status = payment_status.value
        else:
            payment_status = str(payment_status).lower()
        
        payment_mode = order.payment_mode
        if payment_mode is None:
            payment_mode = "cash"
        elif hasattr(payment_mode, 'value'):
            payment_mode = payment_mode.value
        else:
            payment_mode = str(payment_mode).lower()
        
        order_dict = {
            "id": order.id,
            "order_number": order.order_number,
            "timestamp": order.timestamp,
            "customer_name": order.customer_name,
            "food_preparation_stage": food_stage,
            "payment_status": payment_status,
            "payment_mode": payment_mode,
            "total_amount": order.total_amount,
            "created_at": order.created_at
        }
        result.append(order_dict)
    return result


@app.get("/api/orders/{order_id}", response_model=schemas.Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    return db_order


@app.get("/api/orders/number/{order_number}", response_model=schemas.Order)
def read_order_by_number(order_number: str, db: Session = Depends(get_db)):
    db_order = crud.get_order_by_number(db, order_number=order_number)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with number {order_number} not found"
        )
    return db_order


@app.get("/api/orders/", response_model=List[schemas.OrderSummary])
def read_orders(
    skip: int = 0, 
    limit: int = 100,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    mode_of_order: Optional[models.OrderMode] = None,
    payment_mode: Optional[models.PaymentMode] = None,
    time_of_day: Optional[str] = None,
    item_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    orders = crud.get_orders(
        db, 
        skip=skip, 
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        mode_of_order=mode_of_order,
        payment_mode=payment_mode,
        time_of_day=time_of_day,
        item_id=item_id
    )
    return orders


@app.put("/api/orders/{order_id}", response_model=schemas.Order)
def update_order(
    order_id: int, 
    order_update: schemas.OrderUpdate, 
    db: Session = Depends(get_db)
):
    db_order = crud.update_order(db, order_id=order_id, order_update=order_update)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    return db_order


@app.delete("/api/orders/{order_number}")
def delete_order(order_number: str, db: Session = Depends(get_db)):
    """Soft delete an order by order_number (e.g., NV-20251109-0003)"""
    db_order = crud.soft_delete_order_by_number(db, order_number=order_number)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with number {order_number} not found or already deleted"
        )
    return {
        "message": f"Order {db_order.order_number} has been deleted successfully",
        "order_id": db_order.id,
        "order_number": db_order.order_number,
        "deleted_at": db_order.deleted_at.isoformat() if db_order.deleted_at else None
    }


# Analytics endpoints
@app.get("/api/analytics/summary")
def get_analytics_summary(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    return crud.get_analytics_summary(db, date_from=date_from, date_to=date_to)


@app.get("/api/analytics/top-items")
def get_top_selling_items(
    limit: int = 10,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    return crud.get_top_selling_items(
        db, 
        limit=limit,
        date_from=date_from,
        date_to=date_to
    )


@app.get("/api/analytics/sales-by-time")
def get_sales_by_time(
    time_unit: str = Query("day", enum=["hour", "day", "week", "month"]),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    return crud.get_sales_by_time_unit(
        db, 
        time_unit=time_unit,
        date_from=date_from,
        date_to=date_to
    )


@app.get("/api/analytics/customers")
def get_customer_details(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    return crud.get_customer_details(
        db,
        date_from=date_from,
        date_to=date_to
    )


@app.get("/api/customers/autocomplete")
def get_customer_autocomplete(
    search: Optional[str] = Query(None, description="Search query for customer name or phone"),
    db: Session = Depends(get_db)
):
    """Get customer name and phone suggestions for autocomplete"""
    return crud.get_customer_autocomplete(db, search_query=search)


@app.put("/api/orders/{order_id}/status", response_model=schemas.Order)
def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update order status (preparation stage, payment status, and/or payment mode)"""
    db_order = crud.update_order_status(
        db,
        order_id=order_id,
        food_preparation_stage=status_update.food_preparation_stage,
        payment_status=status_update.payment_status,
        payment_mode=status_update.payment_mode
    )
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    return db_order


@app.post("/api/orders/{order_id}/mark-paid", response_model=schemas.Order)
def mark_order_as_paid(order_id: int, db: Session = Depends(get_db)):
    """Mark an order as payment completed"""
    db_order = crud.update_order_status(
        db,
        order_id=order_id,
        payment_status=PaymentStatus.PAYMENT_DONE
    )
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    return db_order


# Expense endpoints
@app.post("/api/expenses/", response_model=schemas.ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    """Create a new expense"""
    return crud.create_expense(db=db, expense=expense)


@app.get("/api/expenses/", response_model=schemas.ExpenseListResponse)
def list_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    date_from: Optional[date] = Query(None, description="Filter expenses from this date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter expenses to this date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    expense_type: Optional[str] = Query(None, description="Filter by expense type (one-time or recurrent)"),
    payment_mode: Optional[str] = Query(None, description="Filter by payment mode"),
    db: Session = Depends(get_db)
):
    """List expenses with optional filters"""
    expenses, total = crud.list_expenses(
        db=db,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        category=category,
        expense_type=expense_type,
        payment_mode=payment_mode
    )
    return schemas.ExpenseListResponse(
        expenses=expenses,
        total=total,
        skip=skip,
        limit=limit
    )


@app.get("/api/expenses/summary", response_model=schemas.ExpenseSummary)
def get_expense_summary(
    date_from: Optional[date] = Query(None, description="Start date for summary (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date for summary (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get expense summary with totals and breakdowns by category and month"""
    summary = crud.get_expense_summary(db=db, date_from=date_from, date_to=date_to)
    # FastAPI will automatically validate and serialize the dict using the response_model
    return summary


@app.get("/api/expenses/{expense_id}", response_model=schemas.ExpenseOut)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    """Get a single expense by ID"""
    db_expense = crud.get_expense(db, expense_id=expense_id)
    if db_expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} not found"
        )
    return db_expense


# Customer Balance endpoints
@app.get("/api/customers/balance")
def get_customer_balance(
    name: str = Query(..., description="Customer name"),
    phone: Optional[str] = Query(None, description="Customer phone (optional)"),
    db: Session = Depends(get_db)
):
    """Get customer balance by name and optionally phone"""
    balance = crud.get_customer_balance_by_name(db, name, phone)
    if balance is None:
        # Customer doesn't exist, return 0 balance
        return {"balance": Decimal('0'), "exists": False}
    return {"balance": balance, "exists": True}


@app.get("/api/customers/", response_model=List[schemas.Customer])
def get_all_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """Get all customers with their balances"""
    return crud.get_all_customers(db, skip=skip, limit=limit)


@app.post("/api/customers/{customer_id}/balance", response_model=schemas.Customer)
def update_customer_balance(
    customer_id: int,
    balance_update: schemas.CustomerBalanceUpdate,
    db: Session = Depends(get_db)
):
    """Manually update customer balance with optional reason"""
    customer = crud.update_customer_balance(db, customer_id, balance_update.balance, balance_update.reason)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    return customer


@app.post("/api/customers/{customer_id}/payment", response_model=schemas.Customer)
def add_customer_payment(
    customer_id: int,
    payment: schemas.CustomerPaymentAdd,
    db: Session = Depends(get_db)
):
    """Add payment to customer balance (increases balance/credit)"""
    customer = crud.add_customer_payment(db, customer_id, payment.amount, payment.notes)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    return customer


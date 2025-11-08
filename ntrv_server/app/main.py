from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import os

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, models, schemas, utils
from app.db import get_db, init_db
from app.config import settings

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


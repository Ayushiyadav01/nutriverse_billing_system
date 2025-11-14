#!/usr/bin/env python3
"""
Script to seed sample expense data into the database.
Run this script to populate the database with sample expenses for testing.
"""

from datetime import date, timedelta
from decimal import Decimal
import random

from sqlalchemy.orm import Session

from app.models import Expense, get_ist_now
from app.db import SessionLocal, init_db
from app.crud import create_expense
from app.schemas import ExpenseCreate

# Sample expense data
SAMPLE_EXPENSES = [
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Monthly Rent Payment",
        "category": "Rent",
        "expense_type": "recurrent",
        "amount": Decimal("25000.00"),
        "payment_mode": "cash",
        "vendor": "Property Owner",
        "notes": "Monthly rent for the restaurant space"
    },
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Raw Vegetables Purchase",
        "category": "Raw Materials",
        "expense_type": "one-time",
        "amount": Decimal("8500.00"),
        "payment_mode": "upi",
        "vendor": "Fresh Market Suppliers",
        "notes": "Weekly vegetable procurement"
    },
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Packaging Materials",
        "category": "Packaging",
        "expense_type": "one-time",
        "amount": Decimal("3200.00"),
        "payment_mode": "card",
        "vendor": "Packaging Solutions Ltd",
        "notes": "Food containers and bags"
    },
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Electricity Bill",
        "category": "Utilities",
        "expense_type": "recurrent",
        "amount": Decimal("4500.00"),
        "payment_mode": "upi",
        "vendor": "Electricity Board",
        "notes": "Monthly electricity charges"
    },
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Staff Salary - November",
        "category": "Staff Salary",
        "expense_type": "recurrent",
        "amount": Decimal("45000.00"),
        "payment_mode": "card",
        "vendor": "Bank Transfer",
        "notes": "Monthly salary for kitchen and service staff"
    },
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Delivery Service Fee",
        "category": "Logistics",
        "expense_type": "recurrent",
        "amount": Decimal("1500.00"),
        "payment_mode": "upi",
        "vendor": "QuickDeliver",
        "notes": "Monthly subscription for delivery service"
    },
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Social Media Marketing",
        "category": "Marketing",
        "expense_type": "one-time",
        "amount": Decimal("5000.00"),
        "payment_mode": "card",
        "vendor": "Digital Marketing Agency",
        "notes": "Facebook and Instagram ads campaign"
    },
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Kitchen Equipment Repair",
        "category": "Maintenance",
        "expense_type": "one-time",
        "amount": Decimal("2800.00"),
        "payment_mode": "cash",
        "vendor": "Equipment Repair Services",
        "notes": "Oven and refrigerator maintenance"
    },
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Spices and Condiments",
        "category": "Raw Materials",
        "expense_type": "one-time",
        "amount": Decimal("2200.00"),
        "payment_mode": "cash",
        "vendor": "Spice Wholesaler",
        "notes": "Bulk purchase of spices"
    },
    {
        "date": date.today() - timedelta(days=random.randint(0, 30)),
        "title": "Water Bill",
        "category": "Utilities",
        "expense_type": "recurrent",
        "amount": Decimal("1200.00"),
        "payment_mode": "upi",
        "vendor": "Water Supply Department",
        "notes": "Monthly water charges"
    }
]


def seed_expenses(db: Session):
    """Seed sample expenses into the database"""
    print("Seeding sample expenses...")
    
    created_count = 0
    for expense_data in SAMPLE_EXPENSES:
        try:
            expense_create = ExpenseCreate(**expense_data)
            create_expense(db, expense_create)
            created_count += 1
            print(f"✓ Created expense: {expense_data['title']}")
        except Exception as e:
            print(f"✗ Failed to create expense '{expense_data['title']}': {str(e)}")
    
    print(f"\nSuccessfully created {created_count} out of {len(SAMPLE_EXPENSES)} sample expenses.")
    return created_count


def main():
    """Main function to run the seed script"""
    print("=" * 60)
    print("Expense Seeding Script")
    print("=" * 60)
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized")
    
    # Create database session
    db = SessionLocal()
    try:
        # Seed expenses
        print("\nStarting expense seeding...")
        created_count = seed_expenses(db)
        
        print("\n" + "=" * 60)
        print(f"Seeding completed! Created {created_count} expenses.")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Error during seeding: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()



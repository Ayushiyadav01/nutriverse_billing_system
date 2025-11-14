"""
Unit tests for Expense CRUD operations and API endpoints.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db import Base, get_db
from app.main import app
from app.models import Expense, ExpenseType
from app.schemas import ExpenseCreate, ExpenseUpdate
from app.crud import (
    create_expense,
    get_expense,
    list_expenses,
    update_expense,
    delete_expense,
    get_expense_summary
)


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_expenses.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_expense_data():
    """Sample expense data for testing"""
    return {
        "date": date.today(),
        "title": "Test Expense",
        "category": "Raw Materials",
        "expense_type": ExpenseType.ONE_TIME,
        "amount": Decimal("1000.00"),
        "payment_mode": "cash",
        "vendor": "Test Vendor",
        "notes": "Test notes"
    }


class TestExpenseCRUD:
    """Test Expense CRUD operations"""
    
    def test_create_expense(self, db_session, sample_expense_data):
        """Test creating an expense"""
        expense_create = ExpenseCreate(**sample_expense_data)
        expense = create_expense(db_session, expense_create)
        
        assert expense.id is not None
        assert expense.title == sample_expense_data["title"]
        assert expense.amount == sample_expense_data["amount"]
        assert expense.category == sample_expense_data["category"]
    
    def test_get_expense(self, db_session, sample_expense_data):
        """Test getting an expense by ID"""
        expense_create = ExpenseCreate(**sample_expense_data)
        created_expense = create_expense(db_session, expense_create)
        
        retrieved_expense = get_expense(db_session, created_expense.id)
        assert retrieved_expense is not None
        assert retrieved_expense.id == created_expense.id
        assert retrieved_expense.title == sample_expense_data["title"]
    
    def test_list_expenses(self, db_session, sample_expense_data):
        """Test listing expenses"""
        # Create multiple expenses
        for i in range(3):
            expense_data = sample_expense_data.copy()
            expense_data["title"] = f"Test Expense {i+1}"
            expense_create = ExpenseCreate(**expense_data)
            create_expense(db_session, expense_create)
        
        expenses, total = list_expenses(db_session)
        assert total == 3
        assert len(expenses) == 3
    
    def test_list_expenses_with_filters(self, db_session, sample_expense_data):
        """Test listing expenses with filters"""
        # Create expenses with different categories
        categories = ["Raw Materials", "Packaging", "Utilities"]
        for cat in categories:
            expense_data = sample_expense_data.copy()
            expense_data["category"] = cat
            expense_create = ExpenseCreate(**expense_data)
            create_expense(db_session, expense_create)
        
        # Filter by category
        expenses, total = list_expenses(db_session, category="Raw Materials")
        assert total == 1
        assert expenses[0].category == "Raw Materials"
        
        # Filter by expense type
        expenses, total = list_expenses(db_session, expense_type="one-time")
        assert total == 3
    
    def test_update_expense(self, db_session, sample_expense_data):
        """Test updating an expense"""
        expense_create = ExpenseCreate(**sample_expense_data)
        created_expense = create_expense(db_session, expense_create)
        
        # Update expense
        update_data = ExpenseUpdate(title="Updated Title", amount=Decimal("2000.00"))
        updated_expense = update_expense(db_session, created_expense.id, update_data)
        
        assert updated_expense is not None
        assert updated_expense.title == "Updated Title"
        assert updated_expense.amount == Decimal("2000.00")
    
    def test_delete_expense(self, db_session, sample_expense_data):
        """Test deleting an expense"""
        expense_create = ExpenseCreate(**sample_expense_data)
        created_expense = create_expense(db_session, expense_create)
        
        # Delete expense
        deleted_expense = delete_expense(db_session, created_expense.id)
        assert deleted_expense is not None
        assert deleted_expense.id == created_expense.id
        
        # Verify expense is deleted
        retrieved_expense = get_expense(db_session, created_expense.id)
        assert retrieved_expense is None
    
    def test_get_expense_summary(self, db_session, sample_expense_data):
        """Test getting expense summary"""
        # Create expenses with different categories
        categories = ["Raw Materials", "Packaging", "Raw Materials"]
        amounts = [Decimal("1000.00"), Decimal("2000.00"), Decimal("1500.00")]
        
        for cat, amt in zip(categories, amounts):
            expense_data = sample_expense_data.copy()
            expense_data["category"] = cat
            expense_data["amount"] = amt
            expense_create = ExpenseCreate(**expense_data)
            create_expense(db_session, expense_create)
        
        summary = get_expense_summary(db_session)
        
        assert summary["total_expenses"] == Decimal("4500.00")
        assert summary["total_count"] == 3
        assert len(summary["by_category"]) == 2  # Two unique categories
        
        # Check category totals
        category_totals = {cat["category"]: cat["total_amount"] for cat in summary["by_category"]}
        assert category_totals["Raw Materials"] == Decimal("2500.00")
        assert category_totals["Packaging"] == Decimal("2000.00")


class TestExpenseAPI:
    """Test Expense API endpoints"""
    
    def test_create_expense_api(self, client, sample_expense_data):
        """Test POST /api/expenses/ endpoint"""
        response = client.post("/api/expenses/", json=sample_expense_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_expense_data["title"]
        assert data["id"] is not None
    
    def test_get_expense_api(self, client, sample_expense_data):
        """Test GET /api/expenses/{id} endpoint"""
        # Create expense first
        create_response = client.post("/api/expenses/", json=sample_expense_data)
        expense_id = create_response.json()["id"]
        
        # Get expense
        response = client.get(f"/api/expenses/{expense_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == expense_id
        assert data["title"] == sample_expense_data["title"]
    
    def test_list_expenses_api(self, client, sample_expense_data):
        """Test GET /api/expenses/ endpoint"""
        # Create multiple expenses
        for i in range(3):
            expense_data = sample_expense_data.copy()
            expense_data["title"] = f"Test Expense {i+1}"
            client.post("/api/expenses/", json=expense_data)
        
        # List expenses
        response = client.get("/api/expenses/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["expenses"]) == 3
    
    def test_list_expenses_with_filters_api(self, client, sample_expense_data):
        """Test GET /api/expenses/ with filters"""
        # Create expenses with different categories
        categories = ["Raw Materials", "Packaging"]
        for cat in categories:
            expense_data = sample_expense_data.copy()
            expense_data["category"] = cat
            client.post("/api/expenses/", json=expense_data)
        
        # Filter by category
        response = client.get("/api/expenses/?category=Raw Materials")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["expenses"][0]["category"] == "Raw Materials"
    
    def test_update_expense_api(self, client, sample_expense_data):
        """Test PUT /api/expenses/{id} endpoint"""
        # Create expense first
        create_response = client.post("/api/expenses/", json=sample_expense_data)
        expense_id = create_response.json()["id"]
        
        # Update expense
        update_data = {"title": "Updated Title", "amount": 2000.00}
        response = client.put(f"/api/expenses/{expense_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert float(data["amount"]) == 2000.00
    
    def test_delete_expense_api(self, client, sample_expense_data):
        """Test DELETE /api/expenses/{id} endpoint"""
        # Create expense first
        create_response = client.post("/api/expenses/", json=sample_expense_data)
        expense_id = create_response.json()["id"]
        
        # Delete expense
        response = client.delete(f"/api/expenses/{expense_id}")
        assert response.status_code == 200
        
        # Verify expense is deleted
        get_response = client.get(f"/api/expenses/{expense_id}")
        assert get_response.status_code == 404
    
    def test_get_expense_summary_api(self, client, sample_expense_data):
        """Test GET /api/expenses/summary endpoint"""
        # Create expenses with different categories
        categories = ["Raw Materials", "Packaging", "Raw Materials"]
        amounts = [1000.00, 2000.00, 1500.00]
        
        for cat, amt in zip(categories, amounts):
            expense_data = sample_expense_data.copy()
            expense_data["category"] = cat
            expense_data["amount"] = amt
            client.post("/api/expenses/", json=expense_data)
        
        # Get summary
        response = client.get("/api/expenses/summary")
        assert response.status_code == 200
        data = response.json()
        assert float(data["total_expenses"]) == 4500.00
        assert data["total_count"] == 3
        assert len(data["by_category"]) == 2
    
    def test_create_expense_validation(self, client):
        """Test expense creation validation"""
        # Test missing required fields
        invalid_data = {"title": "Test"}
        response = client.post("/api/expenses/", json=invalid_data)
        assert response.status_code == 422
        
        # Test negative amount
        invalid_data = {
            "date": date.today().isoformat(),
            "title": "Test",
            "category": "Raw Materials",
            "expense_type": "one-time",
            "amount": -100.00
        }
        response = client.post("/api/expenses/", json=invalid_data)
        assert response.status_code == 422



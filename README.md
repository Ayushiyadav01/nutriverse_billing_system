# Nutriverse - The Nurish House

A complete order, billing, and analytics system for a cloud-kitchen / gym-cafeteria.

## Features

- **Menu Management**: Add, edit, and delete menu items with prices, costs, and categories
- **Billing / Orders**: 
  - Create orders with multiple items and quantities
  - Calculate totals, taxes, and discounts
  - Track costs and profits
  - Generate invoices
- **Expenses Management**:
  - Track business expenses with categories (Raw Materials, Packaging, Utilities, Staff Salary, Logistics, Marketing, Rent, Maintenance)
  - Support for one-time and recurrent expenses
  - Filter and view expenses by date range, category, type, and payment mode
  - Expense analytics with category breakdowns and monthly trends
  - Upload and attach bills/receipts to expenses
- **Analytics Dashboard**:
  - Sales metrics and KPIs
  - Visual charts for top-selling items, sales trends, and hourly sales
  - Filterable order history
  - Export data to CSV

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy
- **Frontend**: Streamlit
- **Database**: SQLite (default), with support for PostgreSQL
- **Containerization**: Docker and docker-compose

## Project Structure

```
billing_system/
├── ntrv_server/             # Backend API
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── crud.py          # Database operations
│   │   ├── db.py            # Database connection
│   │   ├── config.py        # Configuration
│   │   ├── utils.py         # Utility functions
│   │   ├── sample_data.py   # Sample data generator
│   │   └── tests/           # Unit tests
│   ├── scripts/             # Helper scripts
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Docker configuration
├── ntrv_frontend/           # Streamlit frontend
│   ├── streamlit_app.py     # Main Streamlit app
│   ├── components/          # UI components
│   │   ├── add_item.py      # Menu management
│   │   ├── billing.py       # Order creation
│   │   └── analysis.py      # Analytics dashboard
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Docker configuration
└── docker-compose.yml       # Docker Compose configuration
```

## Setup Instructions

### Option 1: Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/nutriverse.git
   cd nutriverse
   ```

2. **Set up the backend**:
   ```bash
   cd ntrv_server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python scripts/init_db.py
   ```

4. **Seed sample expense data** (optional):
   ```bash
   python scripts/seed_expenses.py
   ```

5. **Start the backend server**:
   ```bash
   ./scripts/run_backend.sh  # On Windows: python -m uvicorn app.main:app --reload --port 8000
   ```

6. **Set up the frontend** (in a new terminal):
   ```bash
   cd ntrv_frontend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

6. **Start the frontend server**:
   ```bash
   ./scripts/run_frontend.sh  # On Windows: streamlit run streamlit_app.py
   ```

7. **Access the application**:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Docker Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/nutriverse.git
   cd nutriverse
   ```

2. **Create a data directory**:
   ```bash
   mkdir -p data
   ```

3. **Build and start the containers**:
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**:
   ```bash
   docker exec -it nutriverse-backend python scripts/init_db.py
   ```

5. **Access the application**:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Usage Guide

### Menu Management

1. Navigate to the "Menu Management" section
2. Use the "Add Item" tab to create new menu items
3. Use the "View/Edit Items" tab to modify existing items
4. Use the "Import/Export" tab to bulk import/export items via CSV

### Billing

1. Navigate to the "Billing" section
2. Search for items or enter item codes to add to the cart
3. Adjust quantities as needed
4. Enter customer details and select order/payment modes
5. Apply discounts and taxes if applicable
6. Click "Save Order" to create the order
7. View or duplicate previous orders from the "Last Order" section

### Expenses Management

1. Navigate to the "Expenses" section
2. **Add Expense Tab**:
   - Fill in expense details (date, title, category, type, amount, payment mode, vendor, notes)
   - Optionally upload a bill/receipt attachment
   - Click "Add Expense" to save
3. **View Expenses Tab**:
   - Filter expenses by date range, category, expense type, and payment mode
   - View expense list with summary metrics
   - Export expenses to CSV
4. **Analysis Tab**:
   - View expense summary with KPIs (total expenses, percentage change vs prior period, highest category)
   - Visualize expenses by category (pie chart)
   - View monthly expense trends (bar chart)
   - Review category breakdown table

### Analytics

1. Navigate to the "Analysis" section
2. Select date range and other filters
3. View key metrics and charts
4. Export filtered orders to CSV

## API Endpoints

The backend provides the following API endpoints:

- **Menu Items**:
  - `GET /api/menu/` - List all menu items
  - `POST /api/menu/` - Create a new menu item
  - `GET /api/menu/{id}` - Get a specific menu item
  - `PUT /api/menu/{id}` - Update a menu item
  - `DELETE /api/menu/{id}` - Delete a menu item

- **Orders**:
  - `POST /api/orders/` - Create a new order
  - `GET /api/orders/` - List orders with filters
  - `GET /api/orders/{id}` - Get a specific order

- **Expenses**:
  - `POST /api/expenses/` - Create a new expense
  - `GET /api/expenses/` - List expenses with filters (date_from, date_to, category, expense_type, payment_mode, skip, limit)
  - `GET /api/expenses/{id}` - Get a specific expense
  - `PUT /api/expenses/{id}` - Update an expense
  - `DELETE /api/expenses/{id}` - Delete an expense
  - `GET /api/expenses/summary` - Get expense summary with totals and breakdowns by category and month

- **Analytics**:
  - `GET /api/analytics/summary` - Get sales summary
  - `GET /api/analytics/top-items` - Get top-selling items
  - `GET /api/analytics/sales-by-time` - Get sales by time unit

## Extending the Application

### Switching to PostgreSQL

1. Update the `DATABASE_URL` in `ntrv_server/app/config.py`:
   ```python
   DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/nutriverse")
   ```

2. Install PostgreSQL dependencies:
   ```bash
   pip install psycopg2-binary
   ```

3. Update the engine creation in `ntrv_server/app/db.py`:
   ```python
   engine = create_engine(settings.DATABASE_URL)
   ```

### Adding Authentication

1. Implement JWT authentication in FastAPI
2. Add user model and login endpoints
3. Secure API endpoints with dependencies

## Running Tests

```bash
cd ntrv_server
pytest app/tests/

# Run specific test file
pytest app/tests/test_expenses.py -v
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FastAPI for the excellent API framework
- Streamlit for the intuitive UI framework
- SQLAlchemy for the ORM


start server:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
streamlit run streamlit_app.py --server.port 8501



cd /home/ayushi/MyProjects/billing_system/ntrv_server
python3 -m venv venv               # only once if you don’t have a venv yet
source venv/bin/activate          # on Windows use: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


cd /home/ayushi/MyProjects/billing_system/ntrv_frontend
python3 -m venv venv               # only once if needed
pip install -r requirements.txt
source venv/bin/activate          # Windows: venv\Scripts\activate
streamlit run streamlit_app.py --server.port 8501
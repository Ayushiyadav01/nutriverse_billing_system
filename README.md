# Nutriverse - The Nurish House

A complete order, billing, and analytics system for a cloud-kitchen / gym-cafeteria.

## Features

- **Menu Management**: Add, edit, and delete menu items with prices, costs, and categories
- **Billing / Orders**: 
  - Create orders with multiple items and quantities
  - Calculate totals, taxes, and discounts
  - Track costs and profits
  - Generate invoices
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

4. **Start the backend server**:
   ```bash
   ./scripts/run_backend.sh  # On Windows: python -m uvicorn app.main:app --reload --port 8000
   ```

5. **Set up the frontend** (in a new terminal):
   ```bash
   cd ntrv_frontend
   python -m venv venv
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
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FastAPI for the excellent API framework
- Streamlit for the intuitive UI framework
- SQLAlchemy for the ORM


start server:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
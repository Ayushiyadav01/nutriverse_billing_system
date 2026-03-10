import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import os

# API endpoint
API_URL = os.environ.get("API_URL", "http://localhost:8000/api")

# Expense categories from backend
EXPENSE_CATEGORIES = [
    "Raw Materials",
    "Packaging",
    "Utilities",
    "Staff Salary",
    "Logistics",
    "Marketing",
    "Rent",
    "Maintenance",
    "Other"
]

# Directory for expense attachments
ATTACHMENTS_DIR = "data/expense_attachments"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


def create_expense(expense_data: Dict) -> Optional[Dict]:
    """Create a new expense via API"""
    try:
        response = requests.post(f"{API_URL}/expenses/", json=expense_data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error creating expense: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
                st.error(f"API Error: {error_detail}")
            except:
                st.error(f"Status code: {e.response.status_code}")
        return None


def fetch_expenses(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = None,
    expense_type: Optional[str] = None,
    payment_mode: Optional[str] = None,
    skip: int = 0,
    limit: int = 1000
) -> Dict:
    """Fetch expenses from API"""
    params = {"skip": skip, "limit": limit}
    if date_from:
        params["date_from"] = date_from.isoformat()
    if date_to:
        params["date_to"] = date_to.isoformat()
    if category:
        params["category"] = category
    if expense_type:
        params["expense_type"] = expense_type
    if payment_mode:
        params["payment_mode"] = payment_mode
    
    try:
        response = requests.get(f"{API_URL}/expenses/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching expenses: {str(e)}")
        return {"expenses": [], "total": 0, "skip": 0, "limit": 0}


def fetch_expense_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Optional[Dict]:
    """Fetch expense summary from API"""
    params = {}
    if date_from:
        params["date_from"] = date_from.isoformat()
    if date_to:
        params["date_to"] = date_to.isoformat()
    
    try:
        response = requests.get(f"{API_URL}/expenses/summary", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching expense summary: {str(e)}")
        return None


def save_uploaded_file(uploaded_file) -> Optional[str]:
    """Save uploaded file and return the file path"""
    if uploaded_file is not None:
        file_path = os.path.join(ATTACHMENTS_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None


def render_add_expense():
    """Render the Add Expense form"""
    st.subheader("Add New Expense")
    
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            expense_date = st.date_input(
                "Date",
                value=date.today(),
                max_value=date.today(),
                key="expense_date"
            )
            title = st.text_input("Title *", placeholder="e.g., Monthly Rent Payment")
            category = st.selectbox("Category *", options=EXPENSE_CATEGORIES)
            expense_type = st.selectbox(
                "Expense Type *",
                options=["one-time", "recurrent"]
            )
        
        with col2:
            amount = st.number_input(
                "Amount (₹) *",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f"
            )
            payment_mode = st.selectbox(
                "Payment Mode",
                options=["", "cash", "card", "upi", "wallet"],
                index=0
            )
            vendor = st.text_input("Vendor", placeholder="Optional vendor name")
        
        notes = st.text_area("Notes", placeholder="Additional notes about this expense")
        
        uploaded_file = st.file_uploader(
            "Upload Bill/Receipt (Optional)",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="Upload a PDF or image file for this expense"
        )
        
        submitted = st.form_submit_button("Add Expense", type="primary", use_container_width=True)
        
        if submitted:
            if not title or not title.strip():
                st.error("Title is required")
            elif amount <= 0:
                st.error("Amount must be greater than 0")
            else:
                # Save uploaded file if any
                attachment_path = None
                if uploaded_file is not None:
                    attachment_path = save_uploaded_file(uploaded_file)
                
                # Prepare expense data
                expense_data = {
                    "date": expense_date.isoformat(),
                    "title": title.strip(),
                    "category": category,
                    "expense_type": expense_type,
                    "amount": float(amount),
                    "payment_mode": payment_mode if payment_mode else None,
                    "vendor": vendor.strip() if vendor else None,
                    "notes": notes.strip() if notes else None,
                    "attachment": attachment_path
                }
                
                # Create expense
                result = create_expense(expense_data)
                if result:
                    st.success(f"Expense '{title}' added successfully!")
                    st.balloons()


def render_view_expenses():
    """Render the View Expenses tab"""
    st.subheader("View Expenses")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        date_from = st.date_input(
            "From Date",
            value=date.today() - timedelta(days=30),
            key="expense_view_from_date"
        )
    
    with col2:
        date_to = st.date_input(
            "To Date",
            value=date.today(),
            key="expense_view_to_date"
        )
    
    with col3:
        category_filter = st.selectbox(
            "Category",
            options=["All"] + EXPENSE_CATEGORIES,
            key="expense_view_category"
        )
    
    with col4:
        expense_type_filter = st.selectbox(
            "Expense Type",
            options=["All", "one-time", "recurrent"],
            key="expense_view_type"
        )
    
    payment_mode_filter = st.selectbox(
        "Payment Mode",
        options=["All", "cash", "card", "upi", "wallet"],
        key="expense_view_payment_mode"
    )
    
    # Fetch expenses
    expenses_data = fetch_expenses(
        date_from=date_from,
        date_to=date_to,
        category=category_filter if category_filter != "All" else None,
        expense_type=expense_type_filter if expense_type_filter != "All" else None,
        payment_mode=payment_mode_filter if payment_mode_filter != "All" else None,
        limit=1000
    )
    
    expenses = expenses_data.get("expenses", [])
    total_count = expenses_data.get("total", 0)
    
    if not expenses:
        st.info("No expenses found for the selected filters.")
    else:
        # Display summary metrics
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Expenses", total_count)
        with col2:
            total_amount = sum(float(e['amount']) for e in expenses)
            st.metric("Total Amount", f"₹{total_amount:,.2f}")
        with col3:
            avg_amount = total_amount / len(expenses) if expenses else 0
            st.metric("Average Amount", f"₹{avg_amount:,.2f}")
        
        st.divider()
        
        # Create DataFrame for display
        expenses_df = pd.DataFrame(expenses)
        expenses_df['date'] = pd.to_datetime(expenses_df['date']).dt.date
        expenses_df['amount'] = expenses_df['amount'].astype(float)
        
        # Reorder and rename columns
        display_columns = ['date', 'title', 'category', 'expense_type', 'amount', 'payment_mode', 'vendor']
        display_df = expenses_df[display_columns].copy()
        display_df.columns = ['Date', 'Title', 'Category', 'Type', 'Amount', 'Payment Mode', 'Vendor']
        
        # Format amount
        display_df['Amount'] = display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
        
        # Display table
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Export to CSV
        csv = expenses_df.to_csv(index=False)
        st.download_button(
            label="Export Expenses to CSV",
            data=csv,
            file_name=f"expenses_{date_from}_{date_to}.csv",
            mime="text/csv",
            use_container_width=True
        )


def render_expense_analysis():
    """Render the Expense Analysis tab"""
    st.subheader("Expense Analysis")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        analysis_date_from = st.date_input(
            "From Date",
            value=date.today() - timedelta(days=90),
            key="expense_analysis_from_date"
        )
    with col2:
        analysis_date_to = st.date_input(
            "To Date",
            value=date.today(),
            key="expense_analysis_to_date"
        )
    
    # Fetch summary
    summary = fetch_expense_summary(
        date_from=analysis_date_from,
        date_to=analysis_date_to
    )
    
    if not summary:
        st.info("No expense data available for analysis.")
        return
    
    # KPI Cards
    st.divider()
    st.subheader("Key Metrics")
    
    total_expenses = float(summary.get("total_expenses", 0))
    total_count = summary.get("total_count", 0)
    
    # Calculate previous period for comparison
    period_days = (analysis_date_to - analysis_date_from).days
    prev_date_from = analysis_date_from - timedelta(days=period_days + 1)
    prev_date_to = analysis_date_from - timedelta(days=1)
    
    prev_summary = fetch_expense_summary(
        date_from=prev_date_from,
        date_to=prev_date_to
    )
    prev_total = float(prev_summary.get("total_expenses", 0)) if prev_summary else 0
    
    # Calculate percentage change
    pct_change = 0
    if prev_total > 0:
        pct_change = ((total_expenses - prev_total) / prev_total) * 100
    elif total_expenses > 0:
        pct_change = 100  # New expenses
    
    # Find highest category
    by_category = summary.get("by_category", [])
    highest_category = "N/A"
    highest_amount = 0
    if by_category:
        highest_category = by_category[0].get("category", "N/A")
        highest_amount = float(by_category[0].get("total_amount", 0))
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric(
            "Total Expenses",
            f"₹{total_expenses:,.2f}",
            delta=f"{pct_change:.1f}%" if prev_total > 0 else None
        )
    with metric_col2:
        st.metric("Total Count", total_count)
    with metric_col3:
        st.metric(
            "Highest Category",
            highest_category,
            delta=f"₹{highest_amount:,.2f}" if highest_amount > 0 else None
        )
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Expenses by Category")
        if by_category:
            category_df = pd.DataFrame(by_category)
            category_df['total_amount'] = category_df['total_amount'].astype(float)
            
            fig_pie = px.pie(
                category_df,
                values='total_amount',
                names='category',
                title="Expense Distribution by Category"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No category data available")
    
    with col2:
        st.subheader("Expenses by Month")
        by_month = summary.get("by_month", [])
        if by_month:
            month_df = pd.DataFrame(by_month)
            month_df['total_amount'] = month_df['total_amount'].astype(float)
            month_df = month_df.sort_values('month')
            
            fig_bar = px.bar(
                month_df,
                x='month',
                y='total_amount',
                title="Monthly Expense Trend",
                labels={'month': 'Month', 'total_amount': 'Amount (₹)'}
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No monthly data available")
    
    # Category breakdown table
    st.divider()
    st.subheader("Category Breakdown")
    if by_category:
        category_table_df = pd.DataFrame(by_category)
        category_table_df['total_amount'] = category_table_df['total_amount'].astype(float)
        category_table_df['percentage'] = (category_table_df['total_amount'] / total_expenses * 100).round(2)
        category_table_df.columns = ['Category', 'Total Amount', 'Count', 'Percentage']
        category_table_df['Total Amount'] = category_table_df['Total Amount'].apply(lambda x: f"₹{x:,.2f}")
        category_table_df['Percentage'] = category_table_df['Percentage'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            category_table_df,
            use_container_width=True,
            hide_index=True
        )


def render_expenses():
    """Main function to render the Expenses page"""
    st.header("Expenses Management")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Add Expense", "View Expenses", "Analysis"])
    
    with tab1:
        render_add_expense()
    
    with tab2:
        render_view_expenses()
    
    with tab3:
        render_expense_analysis()


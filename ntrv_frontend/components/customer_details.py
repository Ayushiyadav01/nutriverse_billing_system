import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add parent directory to path to import settings
sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import settings

# API endpoint
API_URL = settings.API_URL

def fetch_customer_details(date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> List[Dict]:
    """Fetch customer details from API"""
    params = {}
    if date_from:
        params['date_from'] = date_from.isoformat()
    if date_to:
        params['date_to'] = date_to.isoformat()
    
    try:
        response = requests.get(f"{API_URL}/analytics/customers", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching customer details: {str(e)}")
        return []

def render_customer_details():
    st.header("Customer Details")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.now().date()
        start_date = st.date_input(
            "Start Date",
            value=None,
            max_value=today,
            key="customer_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=None,
            max_value=today,
            min_value=start_date if start_date else None,
            key="customer_end_date"
        )
    
    # Convert to datetime
    date_from = None
    date_to = None
    if start_date:
        date_from = datetime.combine(start_date, datetime.min.time())
    if end_date:
        date_to = datetime.combine(end_date, datetime.max.time())
    
    # Fetch customer details
    customers = fetch_customer_details(date_from, date_to)
    
    if not customers:
        st.info("No customer data found")
    else:
        # Convert to DataFrame
        df = pd.DataFrame(customers)
        
        # Format the total_purchased column
        df['Total Purchased'] = df['total_purchased'].apply(lambda x: f"₹{float(x):,.2f}")
        df['Total Orders'] = df['total_orders']
        
        # Reorder columns for display
        display_df = df[['customer_name', 'phone', 'Total Purchased', 'Total Orders']]
        display_df.columns = ['Customer Name', 'Phone', 'Total Purchased', 'Total Orders']
        
        # Display summary
        st.subheader("Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Customers", len(customers))
        with col2:
            total_revenue = sum(float(c['total_purchased']) for c in customers)
            st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
        with col3:
            total_orders = sum(c['total_orders'] for c in customers)
            st.metric("Total Orders", total_orders)
        
        st.divider()
        
        # Display customer table
        st.subheader("Customer List")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Export to CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Export to CSV",
            data=csv,
            file_name=f"customer_details_{start_date}_{end_date if end_date else 'all'}.csv",
            mime="text/csv"
        )

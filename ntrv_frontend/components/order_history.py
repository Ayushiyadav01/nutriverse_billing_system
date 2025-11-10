import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# API endpoint
API_URL = "http://localhost:8000/api"

def fetch_orders(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Dict]:
    """Fetch orders with filters from API"""
    params = {'skip': skip, 'limit': limit}
    
    if date_from:
        params['date_from'] = date_from.isoformat()
    if date_to:
        params['date_to'] = date_to.isoformat()
    
    try:
        response = requests.get(f"{API_URL}/orders/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching orders: {str(e)}")
        return []

def fetch_order_details(order_id: int) -> Optional[Dict]:
    """Fetch detailed order information"""
    try:
        response = requests.get(f"{API_URL}/orders/{order_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching order details: {str(e)}")
        return None

def render_order_history():
    st.header("Order History")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.now().date()
        start_date = st.date_input(
            "Start Date",
            value=None,
            max_value=today,
            key="order_history_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=None,
            max_value=today,
            min_value=start_date if start_date else None,
            key="order_history_end_date"
        )
    
    # Convert to datetime
    date_from = None
    date_to = None
    if start_date:
        date_from = datetime.combine(start_date, datetime.min.time())
    if end_date:
        date_to = datetime.combine(end_date, datetime.max.time())
    
    # Fetch orders
    orders = fetch_orders(date_from, date_to, limit=1000)
    
    if not orders:
        st.info("No orders found")
    else:
        # Display summary
        st.subheader("Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Orders", len(orders))
        with col2:
            total_amount = sum(float(o['total_amount']) for o in orders)
            st.metric("Total Amount", f"₹{total_amount:,.2f}")
        with col3:
            avg_order = total_amount / len(orders) if orders else 0
            st.metric("Average Order Value", f"₹{avg_order:,.2f}")
        
        st.divider()
        
        # Display orders list
        st.subheader("Orders")
        
        # Create a selectbox to choose an order to view details
        order_options = {f"{o['order_number']} - {o.get('customer_name', 'N/A')} - ₹{float(o['total_amount']):,.2f}": o['id'] 
                        for o in orders}
        
        selected_order_label = st.selectbox(
            "Select Order to View Details",
            options=list(order_options.keys()),
            key="selected_order_history"
        )
        
        if selected_order_label:
            selected_order_id = order_options[selected_order_label]
            order_details = fetch_order_details(selected_order_id)
            
            if order_details:
                st.divider()
                st.subheader("Invoice Details")
                
                # Display order information
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Order Number:** {order_details['order_number']}")
                    # Format the timestamp
                    try:
                        order_date = pd.to_datetime(order_details['timestamp'])
                        formatted_date = order_date.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_date = str(order_details['timestamp'])
                    st.write(f"**Date:** {formatted_date}")
                    st.write(f"**Customer:** {order_details.get('customer_name', 'N/A')}")
                    if order_details.get('phone'):
                        st.write(f"**Phone:** {order_details['phone']}")
                
                with col2:
                    st.write(f"**Total Amount:** ₹{float(order_details['total_amount']):,.2f}")
                    st.write(f"**Payment Mode:** {order_details['payment_mode']}")
                    st.write(f"**Order Mode:** {order_details['mode_of_order']}")
                    if order_details.get('notes'):
                        st.write(f"**Notes:** {order_details['notes']}")
                
                # Display financial breakdown
                st.subheader("Financial Breakdown")
                fin_col1, fin_col2 = st.columns(2)
                with fin_col1:
                    st.write(f"**Subtotal:** ₹{float(order_details['subtotal']):,.2f}")
                    if float(order_details.get('discount_amount', 0)) > 0:
                        st.write(f"**Discount:** ₹{float(order_details['discount_amount']):,.2f}")
                    st.write(f"**Tax:** ₹{float(order_details['tax_amount']):,.2f}")
                with fin_col2:
                    st.write(f"**Making Cost:** ₹{float(order_details['total_making_cost']):,.2f}")
                    st.write(f"**Net Amount:** ₹{float(order_details['net_amount']):,.2f}")
                    st.write(f"**Profit:** ₹{float(order_details['total_profit']):,.2f}")
                
                # Display items
                st.subheader("Items")
                if order_details.get('items'):
                    items_df = pd.DataFrame(order_details['items'])
                    items_df = items_df[['item_name', 'qty', 'unit_price', 'line_total']]
                    items_df.columns = ['Item Name', 'Quantity', 'Unit Price', 'Line Total']
                    items_df['Unit Price'] = items_df['Unit Price'].apply(lambda x: f"₹{float(x):,.2f}")
                    items_df['Line Total'] = items_df['Line Total'].apply(lambda x: f"₹{float(x):,.2f}")
                    
                    st.dataframe(
                        items_df,
                        use_container_width=True,
                        hide_index=True
                    )
        
        st.divider()
        
        # Display orders table
        st.subheader("All Orders")
        orders_df = pd.DataFrame(orders)
        orders_df['Date'] = pd.to_datetime(orders_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        orders_df['Amount'] = orders_df['total_amount'].apply(lambda x: f"₹{float(x):,.2f}")
        
        display_orders_df = orders_df[['order_number', 'Date', 'customer_name', 'Amount', 'payment_mode']]
        display_orders_df.columns = ['Order Number', 'Date', 'Customer', 'Amount', 'Payment Mode']
        
        st.dataframe(
            display_orders_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Export to CSV
        csv = orders_df.to_csv(index=False)
        st.download_button(
            label="Export to CSV",
            data=csv,
            file_name=f"order_history_{start_date}_{end_date if end_date else 'all'}.csv",
            mime="text/csv"
        )

import os
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from typing import List, Dict, Optional

# API endpoint
API_URL = os.environ.get("API_URL", "http://localhost:8000/api")

def fetch_due_payments() -> List[Dict]:
    """Fetch orders with pending or due payments"""
    try:
        response = requests.get(f"{API_URL}/orders/due-payments")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching due payments: {str(e)}")
        return []

def mark_order_as_paid(order_id: int) -> bool:
    """Mark an order as payment completed"""
    try:
        response = requests.post(f"{API_URL}/orders/{order_id}/mark-paid")
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        st.error(f"Error marking order as paid: {str(e)}")
        return False

def update_order_status_api(order_id: int, food_preparation_stage: Optional[str] = None, 
                            payment_status: Optional[str] = None, payment_mode: Optional[str] = None) -> bool:
    """Update order status via API"""
    try:
        update_data = {}
        if food_preparation_stage is not None:
            update_data["food_preparation_stage"] = food_preparation_stage
        if payment_status is not None:
            update_data["payment_status"] = payment_status
        if payment_mode is not None:
            update_data["payment_mode"] = payment_mode
        
        response = requests.put(f"{API_URL}/orders/{order_id}/status", json=update_data)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        st.error(f"Error updating order status: {str(e)}")
        return False

def render_due_payments():
    st.header("Due Payments")
    st.markdown("Orders with **Pending** or **Due** payment status are displayed here.")
    
    due_orders = fetch_due_payments()
    
    if due_orders:
        st.info(f"Found {len(due_orders)} order(s) with pending or due payments.")
        
        # Display orders with payment management
        for order in due_orders:
            with st.container():
                # Order header
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**Order Number:** {order['order_number']}")
                    st.write(f"**Customer:** {order.get('customer_name', 'N/A')}")
                    if order.get('phone'):
                        st.write(f"**Phone:** {order['phone']}")
                
                with col2:
                    st.write(f"**Amount Due:** ₹{float(order['total_amount']):,.2f}")
                    st.write(f"**Status:** {order['payment_status'].replace('_', ' ').title()}")
                    st.write(f"**Order Date:** {order['timestamp']}")
                
                with col3:
                    if st.button("Mark as Paid", key=f"mark_paid_{order['id']}", use_container_width=True, type="primary"):
                        success = mark_order_as_paid(order['id'])
                        if success:
                            st.success(f"Order {order['order_number']} marked as paid!")
                            st.rerun()
                
                # Payment details section
                with st.expander(f"Payment Details - {order['order_number']}"):
                    detail_col1, detail_col2, detail_col3 = st.columns(3)
                    
                    with detail_col1:
                        current_payment_status = order['payment_status']
                        payment_status_options = ["pending", "due", "payment_done", "overpaid", "adjusted"]
                        new_payment_status = st.selectbox(
                            "Payment Status",
                            options=payment_status_options,
                            index=payment_status_options.index(current_payment_status) if current_payment_status in payment_status_options else 0,
                            key=f"due_payment_status_{order['id']}"
                        )
                    
                    with detail_col2:
                        current_payment_mode = order['payment_mode']
                        payment_mode_options = ["cash", "card", "upi", "wallet"]
                        new_payment_mode = st.selectbox(
                            "Payment Mode",
                            options=payment_mode_options,
                            index=payment_mode_options.index(current_payment_mode) if current_payment_mode in payment_mode_options else 0,
                            key=f"due_payment_mode_{order['id']}"
                        )
                    
                    with detail_col3:
                        current_stage = order['food_preparation_stage']
                        new_stage = st.selectbox(
                            "Food Stage",
                            options=["ordered", "preparing", "completed"],
                            index=["ordered", "preparing", "completed"].index(current_stage) if current_stage in ["ordered", "preparing", "completed"] else 0,
                            key=f"due_stage_{order['id']}"
                        )
                    
                    if st.button("Update Order", key=f"update_due_{order['id']}", use_container_width=True):
                        # Check if anything changed
                        changed = False
                        if new_stage != current_stage:
                            changed = True
                        if new_payment_status != current_payment_status:
                            changed = True
                        if new_payment_mode != current_payment_mode:
                            changed = True
                        
                        if changed:
                            success = update_order_status_api(
                                order_id=order['id'],
                                food_preparation_stage=new_stage,
                                payment_status=new_payment_status,
                                payment_mode=new_payment_mode
                            )
                            if success:
                                st.success(f"Order {order['order_number']} updated!")
                                st.rerun()
                
                st.divider()
    else:
        st.success("✅ No orders with pending or due payments. All payments are up to date!")
        
        # Show summary statistics
        st.info("""
        **Note:** Orders with payment status **Pending** or **Due** will appear here.
        Once marked as **Payment Done**, they will be removed from this list.
        """)


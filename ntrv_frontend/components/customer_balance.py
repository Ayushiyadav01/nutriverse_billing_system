import streamlit as st
import pandas as pd
import requests
from typing import Dict, List, Optional
from decimal import Decimal

# API endpoint
API_URL = "http://localhost:8000/api"

def fetch_all_customers() -> List[Dict]:
    """Fetch all customers with their balances"""
    try:
        response = requests.get(f"{API_URL}/customers/")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching customers: {str(e)}")
        return []

def fetch_customer_balance(name: str, phone: Optional[str] = None) -> Optional[Dict]:
    """Fetch customer balance by name and optionally phone"""
    try:
        params = {"name": name}
        if phone:
            params["phone"] = phone
        response = requests.get(f"{API_URL}/customers/balance", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

def add_customer_payment(customer_id: int, amount: float, notes: Optional[str] = None) -> Optional[Dict]:
    """Add payment to customer balance"""
    try:
        data = {"amount": str(amount)}
        if notes:
            data["notes"] = notes
        response = requests.post(
            f"{API_URL}/customers/{customer_id}/payment",
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error adding payment: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
                st.error(f"API Error: {error_detail}")
            except:
                st.error(f"Status code: {e.response.status_code}")
        return None

def update_customer_balance_manual(customer_id: int, new_balance: float) -> Optional[Dict]:
    """Manually update customer balance"""
    try:
        response = requests.post(
            f"{API_URL}/customers/{customer_id}/balance",
            json={"balance": str(new_balance)}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error updating balance: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
                st.error(f"API Error: {error_detail}")
            except:
                st.error(f"Status code: {e.response.status_code}")
        return None

def render_customer_balance():
    """Main function to render the Customer Balance Management page"""
    st.header("💰 Customer Balance Management")
    
    # Create tabs
    tab1, tab2 = st.tabs(["View Balances", "Add Payment"])
    
    with tab1:
        st.subheader("Customer Balances")
        
        # Fetch all customers
        customers = fetch_all_customers()
        
        if not customers:
            st.info("No customers found. Customers will be created automatically when they place orders.")
            return
        
        # Convert to DataFrame for better display
        customers_data = []
        total_credit = 0
        total_owed = 0
        
        for customer in customers:
            balance = float(customer['balance'])
            customers_data.append({
                'ID': customer['id'],
                'Name': customer['name'],
                'Phone': customer['phone'] or 'N/A',
                'Balance': balance,
                'Status': 'Credit' if balance >= 0 else 'Owed'
            })
            if balance >= 0:
                total_credit += balance
            else:
                total_owed += abs(balance)
        
        df = pd.DataFrame(customers_data)
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Customers", len(customers))
        with col2:
            st.metric("Total Credit (Positive)", f"₹{total_credit:,.2f}", delta=None)
        with col3:
            st.metric("Total Owed (Negative)", f"₹{total_owed:,.2f}", delta=None)
        
        st.divider()
        
        # Search and filter
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_query = st.text_input("🔍 Search by name or phone", key="customer_search")
        with search_col2:
            filter_status = st.selectbox("Filter by Status", ["All", "Credit", "Owed"], key="status_filter")
        
        # Filter DataFrame
        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df['Name'].str.contains(search_query, case=False, na=False) |
                filtered_df['Phone'].str.contains(search_query, case=False, na=False)
            ]
        if filter_status != "All":
            filtered_df = filtered_df[filtered_df['Status'] == filter_status]
        
        # Format balance column for display
        display_df = filtered_df.copy()
        display_df['Balance'] = display_df['Balance'].apply(lambda x: f"₹{x:,.2f}")
        
        # Display table
        st.dataframe(
            display_df[['Name', 'Phone', 'Balance', 'Status']],
            use_container_width=True,
            hide_index=True
        )
        
        # Show detailed view for selected customer
        if len(filtered_df) > 0:
            st.divider()
            st.subheader("Customer Details")
            selected_customer_name = st.selectbox(
                "Select customer to view details",
                options=filtered_df['Name'].tolist(),
                key="selected_customer_detail"
            )
            
            if selected_customer_name:
                selected_row = filtered_df[filtered_df['Name'] == selected_customer_name].iloc[0]
                customer_id = selected_row['ID']
                balance = selected_row['Balance']
                
                detail_col1, detail_col2 = st.columns(2)
                with detail_col1:
                    st.write(f"**Customer ID:** {customer_id}")
                    st.write(f"**Name:** {selected_customer_name}")
                    st.write(f"**Phone:** {selected_row['Phone']}")
                with detail_col2:
                    balance_color = "green" if balance >= 0 else "red"
                    balance_text = "Available Credit" if balance >= 0 else "Amount Owed"
                    st.markdown(
                        f"<span style='color: {balance_color}; font-weight: bold; font-size: 1.2em;'>"
                        f"**{balance_text}:** ₹{abs(balance):,.2f}</span>",
                        unsafe_allow_html=True
                    )
    
    with tab2:
        st.subheader("Add Payment")
        st.write("Use this form to record when a customer makes a payment. This will increase their balance (credit).")
        
        # Fetch customers for dropdown
        customers = fetch_all_customers()
        
        if not customers:
            st.info("No customers found. Customers will be created automatically when they place orders.")
        else:
            # Customer selection
            customer_options = {f"{c['name']} ({c['phone'] or 'No phone'})": c for c in customers}
            selected_customer_label = st.selectbox(
                "Select Customer",
                options=list(customer_options.keys()),
                key="payment_customer_select"
            )
            
            if selected_customer_label:
                selected_customer = customer_options[selected_customer_label]
                current_balance = float(selected_customer['balance'])
                
                # Show current balance
                balance_color = "green" if current_balance >= 0 else "red"
                balance_text = "Current Credit" if current_balance >= 0 else "Current Owed"
                st.markdown(
                    f"<span style='color: {balance_color}; font-weight: bold;'>"
                    f"**{balance_text}:** ₹{abs(current_balance):,.2f}</span>",
                    unsafe_allow_html=True
                )
                
                # Payment form
                with st.form("add_payment_form", clear_on_submit=True):
                    payment_amount = st.number_input(
                        "Payment Amount (₹)",
                        min_value=0.01,
                        value=0.01,
                        step=0.01,
                        format="%.2f",
                        help="Enter the amount the customer is paying. This will be added to their balance."
                    )
                    
                    payment_notes = st.text_area(
                        "Notes (Optional)",
                        placeholder="Add any notes about this payment...",
                        height=100
                    )
                    
                    submitted = st.form_submit_button("Add Payment", type="primary", use_container_width=True)
                    
                    if submitted:
                        if payment_amount <= 0:
                            st.error("Payment amount must be greater than 0")
                        else:
                            # Add payment
                            result = add_customer_payment(
                                selected_customer['id'],
                                payment_amount,
                                payment_notes if payment_notes else None
                            )
                            
                            if result:
                                new_balance = float(result['balance'])
                                st.success(
                                    f"✅ Payment of ₹{payment_amount:,.2f} added successfully! "
                                    f"New balance: ₹{new_balance:,.2f}"
                                )
                                # Don't call st.rerun() - let the form's clear_on_submit handle it
                                # The form will clear automatically and Streamlit will rerun naturally


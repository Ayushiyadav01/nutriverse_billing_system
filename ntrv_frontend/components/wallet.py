import streamlit as st
import requests
from decimal import Decimal
from typing import Optional, Dict
import sys
from pathlib import Path

# Add parent directory to path to import settings
sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import settings

# API endpoint
API_URL = settings.API_URL


def lookup_customer(name: str) -> Optional[Dict]:
    """Lookup customer wallet by name"""
    try:
        response = requests.get(f"{API_URL}/wallet/lookup", params={"name": name})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                return None
        st.error(f"Error looking up customer: {str(e)}")
        return None


def add_payment(customer_id: int, amount: float, notes: Optional[str] = None) -> Optional[Dict]:
    """Add payment to customer wallet"""
    try:
        data = {"amount": str(amount)}
        if notes:
            data["notes"] = notes
        response = requests.post(f"{API_URL}/wallet/{customer_id}/payment", json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error adding payment: {str(e)}")
        return None


def add_charge(customer_id: int, amount: float, notes: Optional[str] = None) -> Optional[Dict]:
    """Add charge/due to customer wallet"""
    try:
        data = {"amount": str(amount)}
        if notes:
            data["notes"] = notes
        response = requests.post(f"{API_URL}/wallet/{customer_id}/charge", json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error adding charge: {str(e)}")
        return None


def render_wallet():
    """Render wallet management page"""
    st.header("Customer Wallet Management")
    
    # Customer lookup
    st.subheader("Lookup Customer")
    customer_name = st.text_input(
        "Customer Name",
        key="wallet_customer_name",
        placeholder="Enter customer name..."
    )
    
    if st.button("Lookup", key="wallet_lookup_button", type="primary"):
        if customer_name:
            customer = lookup_customer(customer_name)
            if customer:
                st.session_state["wallet_customer"] = customer
                st.rerun()
            else:
                st.warning(f"Customer '{customer_name}' not found. They will be created when you add their first payment or charge.")
        else:
            st.error("Please enter a customer name")
    
    # Display customer wallet info
    if "wallet_customer" in st.session_state:
        customer = st.session_state["wallet_customer"]
        customer_id = customer["customer_id"]
        balance = float(customer["balance"])
        
        st.divider()
        st.subheader(f"Customer: {customer['name']}")
        if customer.get("phone"):
            st.write(f"**Phone:** {customer['phone']}")
        
        # Display balance
        col1, col2 = st.columns(2)
        with col1:
            if balance >= 0:
                st.success(f"**Wallet Balance (Credit):** ₹{balance:,.2f}")
            else:
                st.error(f"**Due Amount:** ₹{abs(balance):,.2f}")
        
        with col2:
            st.metric("Balance", f"₹{balance:,.2f}")
        
        st.divider()
        
        # Payment and Charge forms
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Add Payment")
            st.caption("Reduces due / Increases wallet balance")
            payment_amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=100.0,
                step=10.0,
                key="payment_amount"
            )
            payment_notes = st.text_input(
                "Notes (optional)",
                key="payment_notes"
            )
            if st.button("Add Payment", key="add_payment_button", type="primary", use_container_width=True):
                result = add_payment(customer_id, payment_amount, payment_notes)
                if result:
                    st.success(result["message"])
                    # Update customer info
                    customer["balance"] = float(result["balance"])
                    st.session_state["wallet_customer"] = customer
                    st.rerun()
        
        with col2:
            st.subheader("Add Charge/Due")
            st.caption("Increases due / Decreases wallet balance")
            charge_amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=100.0,
                step=10.0,
                key="charge_amount"
            )
            charge_notes = st.text_input(
                "Notes (optional)",
                key="charge_notes"
            )
            if st.button("Add Charge", key="add_charge_button", type="primary", use_container_width=True):
                result = add_charge(customer_id, charge_amount, charge_notes)
                if result:
                    st.success(result["message"])
                    # Update customer info
                    customer["balance"] = float(result["balance"])
                    st.session_state["wallet_customer"] = customer
                    st.rerun()
        
        # Clear button
        if st.button("Clear / Lookup Another Customer", key="clear_wallet_button"):
            if "wallet_customer" in st.session_state:
                del st.session_state["wallet_customer"]
            st.rerun()



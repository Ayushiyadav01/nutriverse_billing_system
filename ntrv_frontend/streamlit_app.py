import streamlit as st
import pandas as pd
from components.add_item import render_menu_management
from components.billing import render_billing
from components.analysis import render_analysis
from components.customer_details import render_customer_details
from components.order_history import render_order_history
from components.due_payments import render_due_payments
from components.expense import render_expenses

# Set page config
st.set_page_config(
    page_title="Nutriverse - The Nurish House",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stMetric label {
        font-weight: bold !important;
        color: #333 !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("<h1 class='main-header'>Nutriverse - The Nurish House</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Order, Billing & Analytics System</p>", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Menu Management", "Billing", "Due Payments", "Expenses", "Analysis", "Customer Details", "Order History"])

# Display the selected page
if page == "Menu Management":
    render_menu_management()
elif page == "Billing":
    render_billing()
elif page == "Due Payments":
    render_due_payments()
elif page == "Expenses":
    render_expenses()
elif page == "Analysis":
    render_analysis()
elif page == "Customer Details":
    render_customer_details()
elif page == "Order History":
    render_order_history()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("© 2025 Nutriverse - The Nurish House")


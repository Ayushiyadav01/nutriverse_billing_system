import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import json

# API endpoint
API_URL = "http://localhost:8000/api"

def fetch_menu_items(active_only: bool = True) -> List[Dict]:
    """Fetch menu items from API with caching"""
    # Use session state to cache menu items
    cache_key = f"billing_menu_items_cache_{active_only}"
    
    # Check if we have cached data
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    try:
        response = requests.get(f"{API_URL}/menu/", params={"active_only": active_only})
        response.raise_for_status()
        menu_items = response.json()
        
        # Cache the result
        st.session_state[cache_key] = menu_items
        
        return menu_items
    except requests.RequestException as e:
        st.error(f"Error fetching menu items: {str(e)}")
        return []

def fetch_menu_item_by_code(code: str) -> Optional[Dict]:
    """Fetch a menu item by code"""
    try:
        response = requests.get(f"{API_URL}/menu/code/{code}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

def create_order(order_data: Dict) -> Optional[Dict]:
    """Create a new order via API"""
    try:
        response = requests.post(f"{API_URL}/orders/", json=order_data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error creating order: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
                st.error(f"API Error: {error_detail}")
            except:
                st.error(f"Status code: {e.response.status_code}")
        return None

def fetch_order(order_id: int) -> Optional[Dict]:
    """Fetch an order by ID"""
    try:
        response = requests.get(f"{API_URL}/orders/{order_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching order: {str(e)}")
        return None

def fetch_order_by_number(order_number: str) -> Optional[Dict]:
    """Fetch an order by number"""
    try:
        response = requests.get(f"{API_URL}/orders/number/{order_number}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

def fetch_customer_suggestions(search_query: Optional[str] = None) -> List[Dict]:
    """Fetch customer name and phone suggestions for autocomplete"""
    try:
        params = {}
        if search_query:
            params["search"] = search_query
        response = requests.get(f"{API_URL}/customers/autocomplete", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

def fetch_today_payments() -> float:
    """Fetch total sales for today"""
    try:
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Fetch today's orders
        params = {
            'date_from': today_start.isoformat(),
            'date_to': today_end.isoformat(),
            'limit': 1000
        }
        response = requests.get(f"{API_URL}/orders/", params=params)
        response.raise_for_status()
        orders = response.json()
        
        # Sum up total amounts for all today's orders (regardless of payment status)
        total = sum(float(order['total_amount']) for order in orders)
        return total
    except requests.RequestException as e:
        st.error(f"Error fetching today's sales: {str(e)}")
        return 0.0

def fetch_active_orders() -> List[Dict]:
    """Fetch active orders (Ordered or Preparing, not Payment Done)"""
    try:
        response = requests.get(f"{API_URL}/orders/active")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching active orders: {str(e)}")
        return []

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

def initialize_session_state():
    """Initialize session state variables for billing"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    if 'customer_name' not in st.session_state:
        st.session_state.customer_name = ""
    
    if 'phone' not in st.session_state:
        st.session_state.phone = ""
    
    if 'mode_of_order' not in st.session_state:
        st.session_state.mode_of_order = "in_person"
    
    if 'payment_mode' not in st.session_state:
        st.session_state.payment_mode = "cash"
    
    if 'discount_type' not in st.session_state:
        st.session_state.discount_type = "none"
    
    if 'discount_value' not in st.session_state:
        st.session_state.discount_value = 0.0
    
    if 'tax_percent' not in st.session_state:
        st.session_state.tax_percent = 0.0
    
    if 'notes' not in st.session_state:
        st.session_state.notes = ""
    
    if 'round_to_integer' not in st.session_state:
        st.session_state.round_to_integer = False
    
    if 'last_order_id' not in st.session_state:
        st.session_state.last_order_id = None
    
    if 'last_order_number' not in st.session_state:
        st.session_state.last_order_number = None
    
    if 'cart_updated' not in st.session_state:
        st.session_state.cart_updated = False
    
    if 'code_error' not in st.session_state:
        st.session_state.code_error = None
    
    if 'item_code_input' not in st.session_state:
        st.session_state.item_code_input = ""
    
    if 'code_qty_input' not in st.session_state:
        st.session_state.code_qty_input = 1
    
    if 'selected_customer_suggestion' not in st.session_state:
        st.session_state.selected_customer_suggestion = None
    
    if 'show_invoice' not in st.session_state:
        st.session_state.show_invoice = False

def add_to_cart(menu_item: Dict, qty: int, sold_price: Optional[float] = None):
    """Add an item to the cart"""
    # Check if item already in cart
    for item in st.session_state.cart:
        if item['id'] == menu_item['id']:
            item['qty'] += qty
            # Update sold_price if provided
            if sold_price is not None:
                item['sold_price'] = sold_price
            return
    
    # Add new item
    mrp = float(menu_item['price'])
    cart_item = {
        'id': menu_item['id'],
        'code': menu_item['code'],
        'name': menu_item['name'],
        'price': mrp,  # MRP for reference
        'sold_price': sold_price if sold_price is not None else mrp,  # Sold At price (defaults to MRP)
        'cost': float(menu_item['cost']),
        'qty': qty
    }
    st.session_state.cart.append(cart_item)

def add_to_cart_callback():
    """Callback function for adding item to cart"""
    if 'selected_item_id' in st.session_state and 'selected_qty' in st.session_state:
        # Fetch menu items if not cached
        menu_items = fetch_menu_items(active_only=True)
        if menu_items:
            menu_df = pd.DataFrame(menu_items)
            selected_item_data = menu_df.loc[menu_df['id'] == st.session_state.selected_item_id].iloc[0].to_dict()
            sold_price = st.session_state.get('selected_sold_at', None)
            add_to_cart(selected_item_data, st.session_state.selected_qty, sold_price)
            st.session_state.cart_updated = True

def add_by_code_callback():
    """Callback function for adding item by code"""
    # Get the item code from session state (already stored by the widget)
    item_code = st.session_state.get("item_code_input", "").upper()
    code_qty = st.session_state.get("code_qty_input", 1)
    code_sold_at = st.session_state.get("code_sold_at", None)
    
    if item_code:
        item = fetch_menu_item_by_code(item_code)
        if item:
            add_to_cart(item, code_qty, code_sold_at)
            st.session_state.cart_updated = True
            # Note: We can't directly modify widget values, so we'll just show success
        else:
            st.session_state.code_error = f"Item code {item_code} not found"

def remove_from_cart(index: int):
    """Remove an item from the cart"""
    if 0 <= index < len(st.session_state.cart):
        st.session_state.cart.pop(index)

def update_cart_qty(index: int, qty: int):
    """Update quantity of an item in the cart"""
    if 0 <= index < len(st.session_state.cart):
        if qty <= 0:
            remove_from_cart(index)
        else:
            st.session_state.cart[index]['qty'] = qty

def update_qty_callback():
    """Callback function for updating cart item quantity"""
    if 'cart_update_index' in st.session_state and 'cart_update_qty' in st.session_state:
        update_cart_qty(st.session_state.cart_update_index, st.session_state.cart_update_qty)
        st.session_state.cart_updated = True

def remove_item_callback():
    """Callback function for removing item from cart"""
    if 'cart_remove_index' in st.session_state:
        remove_from_cart(st.session_state.cart_remove_index)
        st.session_state.cart_updated = True

def clear_cart_callback():
    """Callback function for clearing cart"""
    clear_cart()
    st.session_state.cart_updated = True

def calculate_totals() -> Dict:
    """Calculate order totals based on cart and discounts"""
    # Use sold_price if available, otherwise fallback to price (MRP)
    subtotal = sum(item.get('sold_price', item['price']) * item['qty'] for item in st.session_state.cart)
    total_cost = sum(item['cost'] * item['qty'] for item in st.session_state.cart)
    
    # Calculate discount
    discount_amount = 0.0
    if st.session_state.discount_type == "flat":
        discount_amount = min(float(st.session_state.discount_value), subtotal)
    elif st.session_state.discount_type == "percent":
        discount_amount = subtotal * float(st.session_state.discount_value) / 100
    
    # Calculate tax
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * float(st.session_state.tax_percent) / 100
    
    # Calculate final total
    total = taxable_amount + tax_amount
    
    # Round to integer if enabled
    if st.session_state.round_to_integer:
        total = round(total)
    
    # Calculate profit
    net_amount = total - total_cost
    
    return {
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'taxable_amount': taxable_amount,
        'tax_amount': tax_amount,
        'total': total,
        'total_cost': total_cost,
        'net_amount': net_amount
    }

def clear_cart():
    """Clear the cart and reset order fields"""
    st.session_state.cart = []
    st.session_state.customer_name = ""
    st.session_state.phone = ""
    st.session_state.notes = ""
    st.session_state.discount_type = "none"
    st.session_state.discount_value = 0.0

def view_invoice_callback():
    """Callback function for viewing invoice"""
    if 'last_order_id' in st.session_state and st.session_state.last_order_id:
        st.session_state.show_invoice = True

def select_customer_callback():
    """Callback function for selecting a customer from suggestions"""
    if st.session_state.selected_customer_suggestion:
        # Parse the selected customer (format: "name|phone")
        parts = st.session_state.selected_customer_suggestion.split("|")
        if len(parts) >= 2:
            st.session_state.customer_name = parts[0]
            st.session_state.phone = parts[1] if parts[1] else ""
        elif len(parts) == 1:
            st.session_state.customer_name = parts[0]
            st.session_state.phone = ""
        # Reset the selection to allow re-selection
        st.session_state.selected_customer_suggestion = None

def render_billing():
    st.header("Billing")
    
    # Initialize session state
    initialize_session_state()
    
    # Display today's total payment received at the top
    today_payments = fetch_today_payments()
    st.info(f"💰 **Today's Total Sales: ₹{today_payments:,.2f}**")
    st.divider()
    
    # Create two columns - left for cart, right for order details
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Add Items")
        
        # Show cart updated message if applicable
        if st.session_state.cart_updated:
            st.success("Item added to cart!")
            st.session_state.cart_updated = False
        
        # Show code error if applicable
        if st.session_state.code_error:
            st.error(st.session_state.code_error)
            st.session_state.code_error = None
        
        # Add item by search
        menu_items = fetch_menu_items(active_only=True)
        if menu_items:
            menu_df = pd.DataFrame(menu_items)
            
            # Add search functionality
            search_query = st.text_input(
                "🔍 Search Item (by name, code, or category)",
                key="item_search_query",
                placeholder="Type to search..."
            )
            
            # Filter menu items based on search query
            if search_query:
                search_lower = search_query.lower()
                filtered_df = menu_df[
                    menu_df['name'].str.lower().str.contains(search_lower, na=False) |
                    menu_df['code'].str.lower().str.contains(search_lower, na=False) |
                    menu_df['category'].str.lower().str.contains(search_lower, na=False)
                ]
            else:
                filtered_df = menu_df
            
            if len(filtered_df) == 0:
                st.warning("No items found matching your search.")
            else:
                # Create a searchable dropdown with filtered items
                selected_item = st.selectbox(
                    f"Select Item ({len(filtered_df)} items found)",
                    options=filtered_df['id'].tolist(),
                    format_func=lambda x: f"{filtered_df.loc[filtered_df['id'] == x, 'code'].iloc[0]} - {filtered_df.loc[filtered_df['id'] == x, 'name'].iloc[0]} (₹{filtered_df.loc[filtered_df['id'] == x, 'price'].iloc[0]})",
                    key="selected_item_id"
                )
                
                # The selected_item is automatically stored in st.session_state.selected_item_id
                # No need to assign it again
                
                # Get selected item's MRP for display
                selected_item_mrp = float(filtered_df.loc[filtered_df['id'] == selected_item, 'price'].iloc[0])
                
                qty_col1, qty_col2, qty_col3 = st.columns([2, 2, 1])
                with qty_col1:
                    qty = st.number_input("Quantity", min_value=1, value=1, step=1, key="selected_qty")
                with qty_col2:
                    sold_at = st.number_input(
                        "Sold At (₹)",
                        min_value=0.01,
                        value=float(selected_item_mrp),
                        step=1.0,
                        format="%.2f",
                        key="selected_sold_at",
                        help="Actual sale price (defaults to MRP)"
                    )
                with qty_col3:
                    st.write("&nbsp;", unsafe_allow_html=True)
                    st.write("&nbsp;", unsafe_allow_html=True)
                    st.button("Add to Cart", use_container_width=True, on_click=add_to_cart_callback)
        
        # Add item by code
        with st.expander("Add by Code"):
            code_col1, code_col2, code_col3, code_col4 = st.columns([2, 1, 1, 1])
            with code_col1:
                # The value is automatically stored in st.session_state.item_code_input
                # We'll handle uppercase conversion in the callback
                item_code = st.text_input("Item Code", key="item_code_input", value=st.session_state.get("item_code_input", ""))
            with code_col2:
                # The value is automatically stored in st.session_state.code_qty_input
                code_qty = st.number_input("Qty", min_value=1, value=st.session_state.get("code_qty_input", 1), step=1, key="code_qty_input")
            with code_col3:
                # Get MRP if item exists
                code_mrp = None
                if item_code:
                    item = fetch_menu_item_by_code(item_code)
                    if item:
                        code_mrp = float(item['price'])
                code_sold_at = st.number_input(
                    "Sold At",
                    min_value=0.01,
                    value=code_mrp if code_mrp else 0.01,  # Use 0.01 as default instead of 0.0
                    step=1.0,
                    format="%.2f",
                    key="code_sold_at",
                    disabled=code_mrp is None
                )
            with code_col4:
                st.write("&nbsp;", unsafe_allow_html=True)
                st.write("&nbsp;", unsafe_allow_html=True)
                st.button("Add", use_container_width=True, on_click=add_by_code_callback)
        
        # Display cart
        st.subheader("Cart")
        
        if not st.session_state.cart:
            st.info("Cart is empty")
        else:
            # Ensure all items have sold_price (for backward compatibility)
            for item in st.session_state.cart:
                if 'sold_price' not in item:
                    item['sold_price'] = item['price']
            
            # Create a DataFrame from the cart (for reference, but we display manually)
            cart_df = pd.DataFrame(st.session_state.cart)
            cart_df['line_total'] = cart_df['sold_price'] * cart_df['qty']
            
            # Display the cart as a table
            for i, item in enumerate(st.session_state.cart):
                # Ensure sold_price exists (for backward compatibility)
                if 'sold_price' not in item:
                    item['sold_price'] = item['price']
                
                cart_col1, cart_col2, cart_col3, cart_col4, cart_col5, cart_col6, cart_col7 = st.columns([2.5, 1, 1, 1, 1, 1, 0.5])
                
                with cart_col1:
                    st.write(f"**{item['code']} - {item['name']}**")
                    st.caption(f"MRP: ₹{item['price']:.2f}")
                
                with cart_col2:
                    # Sold At price input
                    with st.form(key=f"sold_price_form_{i}", clear_on_submit=False):
                        new_sold_price = st.number_input(
                            "Sold At",
                            min_value=0.01,
                            value=float(item['sold_price']),
                            step=1.0,
                            format="%.2f",
                            key=f"sold_price_input_{i}",
                            label_visibility="collapsed"
                        )
                        submitted_price = st.form_submit_button("✓", use_container_width=True)
                        if submitted_price:
                            item['sold_price'] = new_sold_price
                            st.session_state.cart_updated = True
                            st.rerun()
                
                with cart_col3:
                    # Use a form to handle quantity updates without infinite loops
                    with st.form(key=f"qty_form_{i}", clear_on_submit=False):
                        new_qty = st.number_input("Quantity", min_value=1, value=item['qty'], step=1, key=f"qty_input_{i}", label_visibility="collapsed")
                        submitted = st.form_submit_button("✓", use_container_width=True)
                        if submitted:
                            update_cart_qty(i, new_qty)
                            st.session_state.cart_updated = True
                            st.rerun()
                
                with cart_col4:
                    line_total = item['sold_price'] * item['qty']
                    st.write(f"**₹{line_total:.2f}**")
                
                with cart_col5:
                    # Show price difference if sold_price differs from MRP
                    if item['sold_price'] != item['price']:
                        diff = item['sold_price'] - item['price']
                        if diff < 0:
                            st.caption(f"↓ ₹{abs(diff):.2f}")
                        else:
                            st.caption(f"↑ ₹{diff:.2f}")
                    else:
                        st.caption("MRP")
                
                with cart_col6:
                    st.write("&nbsp;", unsafe_allow_html=True)
                
                with cart_col7:
                    if st.button("🗑️", key=f"remove_{i}"):
                        remove_from_cart(i)
                        st.session_state.cart_updated = True
                        st.rerun()
                
                st.divider()
            
            # Clear cart button
            if st.button("Clear Cart", use_container_width=True):
                clear_cart()
                st.session_state.cart_updated = True
    
    with col2:
        st.subheader("Order Details")
        
        # Customer details with autocomplete
        customer_name_input = st.text_input(
            "Customer Name 🔍", 
            value=st.session_state.customer_name,
            key="customer_name_input",
            placeholder="Start typing to see suggestions..."
        )
        
        # Update customer_name in session state when input changes
        if customer_name_input != st.session_state.customer_name:
            st.session_state.customer_name = customer_name_input
            # Reset selection when user types manually
            if 'last_selected_suggestion' in st.session_state:
                del st.session_state.last_selected_suggestion
        
        # Fetch customer suggestions based on input
        search_query = customer_name_input.strip() if customer_name_input else None
        customer_suggestions = fetch_customer_suggestions(search_query=search_query)
        
        # Show suggestions dropdown if there are suggestions and user has typed something
        if customer_suggestions and search_query and len(search_query) > 0:
            # Create options for selectbox (format: "name|phone")
            suggestion_options = [
                f"{customer['customer_name']}|{customer['phone']}"
                for customer in customer_suggestions
            ]
            
            # Add "None" option at the beginning
            suggestion_options = ["Select a customer..."] + suggestion_options
            
            # Get current index - default to 0 if no previous selection
            current_index = 0
            if 'last_selected_suggestion' in st.session_state:
                if st.session_state.last_selected_suggestion in suggestion_options:
                    current_index = suggestion_options.index(st.session_state.last_selected_suggestion)
            
            selected_suggestion = st.selectbox(
                "Select from existing customers:",
                options=suggestion_options,
                key="customer_suggestion_select",
                index=current_index
            )
            
            # If a customer is selected (not "Select a customer...")
            if selected_suggestion and selected_suggestion != "Select a customer...":
                # Check if this is a new selection
                if selected_suggestion != st.session_state.get("last_selected_suggestion"):
                    # Parse and fill customer details
                    parts = selected_suggestion.split("|")
                    if len(parts) >= 2:
                        st.session_state.customer_name = parts[0]
                        st.session_state.phone = parts[1] if parts[1] else ""
                    elif len(parts) == 1:
                        st.session_state.customer_name = parts[0]
                        st.session_state.phone = ""
                    st.session_state.last_selected_suggestion = selected_suggestion
                    # Trigger rerun to update the text inputs
                    st.rerun()
        
        # Phone number input (will be auto-filled when customer is selected)
        phone_input = st.text_input(
            "Phone", 
            value=st.session_state.phone,
            key="phone_input"
        )
        
        # Update phone in session state
        if phone_input != st.session_state.phone:
            st.session_state.phone = phone_input
        
        # Order mode and payment mode
        order_col1, order_col2 = st.columns(2)
        with order_col1:
            st.session_state.mode_of_order = st.selectbox(
                "Order Mode",
                options=["in_person", "phone", "whatsapp", "streamlit_ui"],
                index=["in_person", "phone", "whatsapp", "streamlit_ui"].index(st.session_state.mode_of_order)
            )
        with order_col2:
            st.session_state.payment_mode = st.selectbox(
                "Payment Mode",
                options=["cash", "card", "upi", "wallet"],
                index=["cash", "card", "upi", "wallet"].index(st.session_state.payment_mode)
            )
        
        # Discount
        st.subheader("Discount & Tax")
        discount_col1, discount_col2 = st.columns(2)
        with discount_col1:
            st.session_state.discount_type = st.selectbox(
                "Discount Type",
                options=["none", "percent", "flat"],
                index=["none", "percent", "flat"].index(st.session_state.discount_type)
            )
        with discount_col2:
            if st.session_state.discount_type != "none":
                st.session_state.discount_value = st.number_input(
                    "Discount Value" if st.session_state.discount_type == "flat" else "Discount %",
                    min_value=0.0,
                    max_value=100.0 if st.session_state.discount_type == "percent" else None,
                    value=float(st.session_state.discount_value),
                    step=0.01 if st.session_state.discount_type == "flat" else 1.0,
                    format="%.2f" if st.session_state.discount_type == "flat" else "%.0f"
                )
        
        # Tax
        tax_col1, tax_col2 = st.columns(2)
        with tax_col1:
            st.session_state.tax_percent = st.number_input(
                "Tax %",
                min_value=0.0,
                max_value=100.0,
                value=float(st.session_state.tax_percent),
                step=0.1,
                format="%.1f"
            )
        with tax_col2:
            st.session_state.round_to_integer = st.checkbox(
                "Round to nearest ₹",
                value=st.session_state.round_to_integer
            )
        
        # Notes
        st.session_state.notes = st.text_area("Notes", value=st.session_state.notes, height=100)
        
        # Calculate and display totals
        if st.session_state.cart:
            totals = calculate_totals()
            
            st.divider()
            st.subheader("Order Summary")
            
            summary_col1, summary_col2 = st.columns(2)
            with summary_col1:
                st.write("Subtotal:")
                if totals['discount_amount'] > 0:
                    st.write("Discount:")
                st.write("Tax:")
                st.write("**Total:**")
            with summary_col2:
                st.write(f"₹{totals['subtotal']:.2f}")
                if totals['discount_amount'] > 0:
                    st.write(f"₹{totals['discount_amount']:.2f}")
                st.write(f"₹{totals['tax_amount']:.2f}")
                st.write(f"**₹{totals['total']:.2f}**")
            
            # Save order button
            if st.button("Save Order", type="primary", use_container_width=True):
                if not st.session_state.cart:
                    st.error("Cannot save an empty order")
                else:
                    # Prepare order data
                    order_items = []
                    for item in st.session_state.cart:
                        item_data = {
                            "menu_item_id": item['id'],
                            "qty": item['qty']
                        }
                        # Add sold_price if it differs from MRP
                        sold_price = item.get('sold_price', item['price'])
                        if sold_price != item['price']:
                            item_data["sold_price"] = str(sold_price)
                        order_items.append(item_data)
                    
                    order_data = {
                        "customer_name": st.session_state.customer_name,
                        "phone": st.session_state.phone,
                        "mode_of_order": st.session_state.mode_of_order,
                        "payment_mode": st.session_state.payment_mode,
                        "notes": st.session_state.notes,
                        "tax_percent": float(st.session_state.tax_percent),
                        "discount": {
                            "type": st.session_state.discount_type,
                            "value": float(st.session_state.discount_value)
                        },
                        "items": order_items
                    }
                    
                    # Create order via API
                    result = create_order(order_data)
                    if result:
                        st.session_state.last_order_id = result['id']
                        st.session_state.last_order_number = result['order_number']
                        st.success(f"Order {result['order_number']} created successfully!")
                        st.balloons()
                        
                        # Clear cart for next order
                        clear_cart()
                        
                        # Show invoice button
                        st.button(
                            "View Invoice",
                            key="view_invoice_after_save",
                            on_click=view_invoice_callback,
                            use_container_width=True
                        )
                        
                        # Show invoice details if requested
                        if st.session_state.show_invoice and st.session_state.last_order_id:
                            with st.expander("Invoice Details", expanded=True):
                                order = fetch_order(st.session_state.last_order_id)
                                if order:
                                    st.write(f"**Order Number:** {order['order_number']}")
                                    st.write(f"**Date:** {order['timestamp']}")
                                    st.write(f"**Customer:** {order.get('customer_name', 'N/A')}")
                                    st.write(f"**Total Amount:** ₹{float(order['total_amount']):,.2f}")
                                    st.write(f"**Payment Mode:** {order['payment_mode']}")
                                    
                                    st.subheader("Items")
                                    invoice_df = pd.DataFrame(order['items'])
                                    # Include sold_price if available
                                    if 'unit_sold_price' in invoice_df.columns:
                                        invoice_df['display_price'] = invoice_df['unit_sold_price'].fillna(invoice_df['unit_price'])
                                        invoice_df = invoice_df[['item_name', 'qty', 'display_price', 'line_total']]
                                        invoice_df.columns = ['Item', 'Qty', 'Sold At', 'Total']
                                    else:
                                        invoice_df = invoice_df[['item_name', 'qty', 'unit_price', 'line_total']]
                                        invoice_df.columns = ['Item', 'Qty', 'Unit Price', 'Total']
                                    st.dataframe(invoice_df, use_container_width=True, hide_index=True)
                                    
                                    st.session_state.show_invoice = False
        
        # Active Orders Management Table
        st.divider()
        st.subheader("Active Orders Management")
        
        active_orders = fetch_active_orders()
        
        if active_orders:
            # Create a DataFrame for display
            orders_data = []
            for order in active_orders:
                orders_data.append({
                    "Order ID": order['id'],
                    "Bill No.": order['order_number'],
                    "Customer": order.get('customer_name', 'N/A'),
                    "Amount": f"₹{float(order['total_amount']):,.2f}",
                    "Timestamp": order['timestamp']
                })
            
            orders_df = pd.DataFrame(orders_data)
            
            # Display orders with editable status
            for idx, order in enumerate(active_orders):
                with st.container():
                    order_col1, order_col2, order_col3, order_col4, order_col5 = st.columns([2, 2, 2, 2, 1])
                    
                    with order_col1:
                        st.write(f"**{order['order_number']}**")
                        st.caption(order.get('customer_name', 'N/A'))
                    
                    with order_col2:
                        current_stage = order['food_preparation_stage']
                        new_stage = st.selectbox(
                            "Stage",
                            options=["ordered", "preparing", "completed"],
                            index=["ordered", "preparing", "completed"].index(current_stage) if current_stage in ["ordered", "preparing", "completed"] else 0,
                            key=f"stage_{order['id']}"
                        )
                    
                    with order_col3:
                        current_payment_status = order['payment_status']
                        payment_status_options = ["pending", "due", "payment_done", "overpaid", "adjusted"]
                        new_payment_status = st.selectbox(
                            "Payment Status",
                            options=payment_status_options,
                            index=payment_status_options.index(current_payment_status) if current_payment_status in payment_status_options else 0,
                            key=f"payment_status_{order['id']}"
                        )
                    
                    with order_col4:
                        current_payment_mode = order['payment_mode']
                        payment_mode_options = ["cash", "card", "upi", "wallet"]
                        new_payment_mode = st.selectbox(
                            "Payment Mode",
                            options=payment_mode_options,
                            index=payment_mode_options.index(current_payment_mode) if current_payment_mode in payment_mode_options else 0,
                            key=f"payment_mode_{order['id']}"
                        )
                    
                    with order_col5:
                        st.write(f"**₹{float(order['total_amount']):,.2f}**")
                        if st.button("Update", key=f"update_{order['id']}", use_container_width=True):
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
            st.info("No active orders to display. Orders with status 'Ordered' or 'Preparing' (and not 'Payment Done' or 'Due') will appear here.")
        
        # Last order actions
        if st.session_state.last_order_number:
            with st.expander("Last Order"):
                st.write(f"Order Number: {st.session_state.last_order_number}")
                
                last_order_col1, last_order_col2 = st.columns(2)
                with last_order_col1:
                    if st.button("View Invoice", key="view_invoice_last_order", use_container_width=True, on_click=view_invoice_callback):
                        pass
                with last_order_col2:
                    if st.button("Duplicate Order", key="duplicate_order", use_container_width=True):
                        # Load last order and populate cart
                        last_order = fetch_order(st.session_state.last_order_id)
                        if last_order:
                            # Clear current cart
                            st.session_state.cart = []
                            
                            # Add items from last order
                            for item in last_order['items']:
                                cart_item = {
                                    'id': item['menu_item_id'],
                                    'code': item['item_name'][:10],  # Use first part of name as code
                                    'name': item['item_name'],
                                    'price': float(item['unit_price']),
                                    'cost': float(item['unit_cost']),
                                    'qty': item['qty']
                                }
                                st.session_state.cart.append(cart_item)
                            
                            # Copy other details
                            st.session_state.customer_name = last_order['customer_name'] or ""
                            st.session_state.phone = last_order['phone'] or ""
                            st.session_state.mode_of_order = last_order['mode_of_order']
                            st.session_state.payment_mode = last_order['payment_mode']
                            st.session_state.discount_type = last_order['discount_type']
                            st.session_state.discount_value = float(last_order['discount_value'])
                            st.session_state.tax_percent = float(last_order['tax_percent'])
                            st.session_state.notes = last_order['notes'] or ""
                            
                            st.session_state.cart_updated = True
                
                # Show invoice details if requested from last order section
                if st.session_state.show_invoice and st.session_state.last_order_id:
                    st.divider()
                    order = fetch_order(st.session_state.last_order_id)
                    if order:
                        st.subheader("Invoice Details")
                        st.write(f"**Order Number:** {order['order_number']}")
                        st.write(f"**Date:** {order['timestamp']}")
                        st.write(f"**Customer:** {order.get('customer_name', 'N/A')}")
                        st.write(f"**Total Amount:** ₹{float(order['total_amount']):,.2f}")
                        st.write(f"**Payment Mode:** {order['payment_mode']}")
                        
                        st.write("**Items:**")
                        invoice_df = pd.DataFrame(order['items'])
                        invoice_df = invoice_df[['item_name', 'qty', 'unit_price', 'line_total']]
                        invoice_df.columns = ['Item', 'Qty', 'Unit Price', 'Total']
                        st.dataframe(invoice_df, use_container_width=True, hide_index=True)
                        
                        st.session_state.show_invoice = False


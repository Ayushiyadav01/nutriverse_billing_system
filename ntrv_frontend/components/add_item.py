import streamlit as st
import pandas as pd
import requests
from typing import Dict, List, Optional
import json

# API endpoint
API_URL = "http://localhost:8000/api"

def fetch_menu_items(active_only: bool = False) -> List[Dict]:
    """Fetch menu items from API with caching"""
    # Use session state to cache menu items
    cache_key = f"menu_items_cache_{active_only}"
    
    # Check if we have cached data and if it's still valid
    if cache_key in st.session_state:
        # Return cached data (you can add timestamp checking here if needed)
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

def create_menu_item(item_data: Dict) -> Optional[Dict]:
    """Create a new menu item via API"""
    try:
        response = requests.post(f"{API_URL}/menu/", json=item_data)
        response.raise_for_status()
        result = response.json()
        
        # Clear cache to force refresh
        if "menu_items_cache_True" in st.session_state:
            del st.session_state["menu_items_cache_True"]
        if "menu_items_cache_False" in st.session_state:
            del st.session_state["menu_items_cache_False"]
        
        return result
    except requests.RequestException as e:
        st.error(f"Error creating menu item: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
                st.error(f"API Error: {error_detail}")
            except:
                st.error(f"Status code: {e.response.status_code}")
        return None

def update_menu_item(item_id: int, item_data: Dict) -> Optional[Dict]:
    """Update an existing menu item via API"""
    try:
        response = requests.put(f"{API_URL}/menu/{item_id}", json=item_data)
        response.raise_for_status()
        result = response.json()
        
        # Clear cache to force refresh
        if "menu_items_cache_True" in st.session_state:
            del st.session_state["menu_items_cache_True"]
        if "menu_items_cache_False" in st.session_state:
            del st.session_state["menu_items_cache_False"]
        
        return result
    except requests.RequestException as e:
        st.error(f"Error updating menu item: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json().get('detail', str(e))
                st.error(f"API Error: {error_detail}")
            except:
                st.error(f"Status code: {e.response.status_code}")
        return None

def delete_menu_item(item_id: int) -> bool:
    """Delete (deactivate) a menu item via API"""
    try:
        response = requests.delete(f"{API_URL}/menu/{item_id}")
        response.raise_for_status()
        
        # Clear cache to force refresh
        if "menu_items_cache_True" in st.session_state:
            del st.session_state["menu_items_cache_True"]
        if "menu_items_cache_False" in st.session_state:
            del st.session_state["menu_items_cache_False"]
        
        return True
    except requests.RequestException as e:
        st.error(f"Error deleting menu item: {str(e)}")
        return False

def delete_item_callback():
    """Callback function for item deletion"""
    if delete_menu_item(st.session_state.item_to_delete):
        st.session_state.delete_success = True
    else:
        st.session_state.delete_success = False

def render_menu_management():
    # Initialize session state variables
    if 'delete_success' not in st.session_state:
        st.session_state.delete_success = None
    
    if 'item_to_delete' not in st.session_state:
        st.session_state.item_to_delete = None
    
    if 'menu_df_hash' not in st.session_state:
        st.session_state.menu_df_hash = None
    
    if 'update_in_progress' not in st.session_state:
        st.session_state.update_in_progress = False
    
    st.header("Menu Management")
    
    # Create tabs for different operations
    tab1, tab2, tab3 = st.tabs(["Add Item", "View/Edit Items", "Import/Export"])
    
    # Tab 1: Add new menu item
    with tab1:
        st.subheader("Add New Menu Item")
        
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                code = st.text_input("Item Code", max_chars=10).upper()
                name = st.text_input("Item Name", max_chars=100)
                category = st.text_input("Category", max_chars=50)
            
            with col2:
                price = st.number_input("Price", min_value=0.0, step=0.01, format="%.2f")
                cost = st.number_input("Cost to Make", min_value=0.0, step=0.01, format="%.2f")
                is_active = st.checkbox("Active", value=True)
            
            submitted = st.form_submit_button("Add Item")
            
            if submitted:
                if not code or not name or not category:
                    st.error("Please fill in all required fields")
                else:
                    item_data = {
                        "code": code,
                        "name": name,
                        "category": category,
                        "price": price,
                        "cost": cost,
                        "is_active": is_active
                    }
                    
                    result = create_menu_item(item_data)
                    if result:
                        st.success(f"Item '{name}' added successfully!")
                        st.balloons()
    
    # Tab 2: View and edit menu items
    with tab2:
        st.subheader("Menu Items")
        
        # Filter options
        col1, col2 = st.columns([1, 3])
        with col1:
            show_active_only = st.checkbox("Show Active Only", value=True, key="show_active_only_filter")
        
        # Reset stored state if filter changed
        if 'last_filter_state' not in st.session_state:
            st.session_state.last_filter_state = show_active_only
        elif st.session_state.last_filter_state != show_active_only:
            st.session_state.last_filter_state = show_active_only
            st.session_state.last_menu_df = None
            st.session_state.update_in_progress = False
        
        # Fetch menu items
        menu_items = fetch_menu_items(active_only=show_active_only)
        
        if not menu_items:
            st.info("No menu items found")
        else:
            # Convert to DataFrame for display
            df = pd.DataFrame(menu_items)
            
            # Reorder and rename columns for display
            display_df = df[['id', 'code', 'name', 'category', 'price', 'cost', 'is_active']].copy()
            
            # Store the original dataframe in session state for comparison
            if 'last_menu_df' not in st.session_state:
                st.session_state.last_menu_df = display_df.copy()
            
            # Display as a table with edit/delete buttons
            edited_df = st.data_editor(
                display_df,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "code": st.column_config.TextColumn("Code"),
                    "name": st.column_config.TextColumn("Name"),
                    "category": st.column_config.TextColumn("Category"),
                    "price": st.column_config.NumberColumn("Price", format="%.2f"),
                    "cost": st.column_config.NumberColumn("Cost", format="%.2f"),
                    "is_active": st.column_config.CheckboxColumn("Active"),
                },
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                key="menu_items_editor"
            )
            
            # Only check for changes if update is not in progress
            if not st.session_state.update_in_progress:
                # Compare with last known state
                try:
                    if st.session_state.last_menu_df is not None and not st.session_state.last_menu_df.equals(edited_df):
                        # Check if there are actual changes by comparing by ID
                        changes_detected = False
                        updated_count = 0
                        
                        # Create a dictionary of original rows by ID for faster lookup
                        original_by_id = {}
                        if st.session_state.last_menu_df is not None:
                            for idx, row in st.session_state.last_menu_df.iterrows():
                                original_by_id[int(row["id"])] = row
                        
                        for index, row in edited_df.iterrows():
                            item_id = int(row["id"])
                            
                            if item_id in original_by_id:
                                original_row = original_by_id[item_id]
                                
                                # Check if any editable field changed
                                if (str(original_row["name"]) != str(row["name"]) or 
                                    str(original_row["category"]) != str(row["category"]) or
                                    abs(float(original_row["price"]) - float(row["price"])) > 0.01 or
                                    abs(float(original_row["cost"]) - float(row["cost"])) > 0.01 or
                                    bool(original_row["is_active"]) != bool(row["is_active"])):
                                    
                                    changes_detected = True
                                    
                                    # Create update payload
                                    update_data = {
                                        "name": str(row["name"]),
                                        "category": str(row["category"]),
                                        "price": float(row["price"]),
                                        "cost": float(row["cost"]),
                                        "is_active": bool(row["is_active"])
                                    }
                                    
                                    # Update via API
                                    result = update_menu_item(item_id, update_data)
                                    if result:
                                        updated_count += 1
                        
                        if changes_detected and updated_count > 0:
                            # Mark update as in progress to prevent re-processing
                            st.session_state.update_in_progress = True
                            st.success(f"{updated_count} item(s) updated successfully!")
                            
                            # Clear cache and reset stored state to force refresh
                            if "menu_items_cache_True" in st.session_state:
                                del st.session_state["menu_items_cache_True"]
                            if "menu_items_cache_False" in st.session_state:
                                del st.session_state["menu_items_cache_False"]
                            
                            # Reset the stored dataframe to force fresh comparison next time
                            st.session_state.last_menu_df = None
                            
                            # Reset the flag - don't call st.rerun() as it causes infinite loops
                            # Streamlit will naturally rerun when needed
                            st.session_state.update_in_progress = False
                        elif not changes_detected:
                            # No actual changes, just update the stored state silently
                            st.session_state.last_menu_df = edited_df.copy()
                    else:
                        # Dataframes are equal or first time, just store the state
                        if st.session_state.last_menu_df is None:
                            st.session_state.last_menu_df = edited_df.copy()
                except Exception as e:
                    # If comparison fails, just update the stored state
                    if st.session_state.last_menu_df is None:
                        st.session_state.last_menu_df = edited_df.copy()
                    st.session_state.update_in_progress = False
            
            # Delete functionality
            with st.expander("Delete Item"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Use session state for the selectbox
                    st.selectbox(
                        "Select Item to Delete",
                        options=df["id"].tolist(),
                        format_func=lambda x: f"{df.loc[df['id'] == x, 'code'].iloc[0]} - {df.loc[df['id'] == x, 'name'].iloc[0]}",
                        key="item_to_delete"
                    )
                with col2:
                    st.write("&nbsp;", unsafe_allow_html=True)
                    st.write("&nbsp;", unsafe_allow_html=True)
                    st.button("Delete", type="primary", use_container_width=True, on_click=delete_item_callback)
                
                # Display success or error message
                if st.session_state.delete_success is True:
                    st.success("Item deleted successfully!")
                    # Reset the flag to avoid showing the message on every rerun
                    st.session_state.delete_success = None
    
    # Tab 3: Import/Export
    with tab3:
        st.subheader("Import/Export Menu Items")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### Export Menu Items")
            if st.button("Export to CSV"):
                menu_items = fetch_menu_items(active_only=False)
                if menu_items:
                    df = pd.DataFrame(menu_items)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="menu_items.csv",
                        mime="text/csv"
                    )
        
        with col2:
            st.write("#### Import Menu Items")
            uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    required_cols = ["code", "name", "category", "price", "cost"]
                    
                    # Check if required columns exist
                    if all(col in df.columns for col in required_cols):
                        st.write("Preview:")
                        st.dataframe(df[required_cols + (["is_active"] if "is_active" in df.columns else [])])
                        
                        if st.button("Import Items"):
                            success_count = 0
                            error_count = 0
                            
                            for _, row in df.iterrows():
                                item_data = {
                                    "code": row["code"],
                                    "name": row["name"],
                                    "category": row["category"],
                                    "price": float(row["price"]),
                                    "cost": float(row["cost"]),
                                    "is_active": bool(row.get("is_active", True))
                                }
                                
                                result = create_menu_item(item_data)
                                if result:
                                    success_count += 1
                                else:
                                    error_count += 1
                            
                            st.success(f"Import completed: {success_count} items added, {error_count} errors")
                            if success_count > 0:
                                st.balloons()
                    else:
                        st.error(f"CSV must contain columns: {', '.join(required_cols)}")
                except Exception as e:
                    st.error(f"Error processing CSV: {str(e)}")


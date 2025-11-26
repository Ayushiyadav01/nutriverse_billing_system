import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import sys
from pathlib import Path

# Add parent directory to path to import settings
sys.path.insert(0, str(Path(__file__).parent.parent))
from settings import settings

# API endpoint
API_URL = settings.API_URL

def fetch_analytics_summary(date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict:
    """Fetch analytics summary from API"""
    params = {}
    if date_from:
        params['date_from'] = date_from.isoformat()
    if date_to:
        params['date_to'] = date_to.isoformat()
    
    try:
        response = requests.get(f"{API_URL}/analytics/summary", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching analytics summary: {str(e)}")
        return {
            "total_orders": 0,
            "total_sales": 0,
            "total_making_cost": 0,
            "total_profit": 0,
            "average_order_value": 0
        }

def fetch_top_items(limit: int = 10, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> List[Dict]:
    """Fetch top selling items from API"""
    params = {'limit': limit}
    if date_from:
        params['date_from'] = date_from.isoformat()
    if date_to:
        params['date_to'] = date_to.isoformat()
    
    try:
        response = requests.get(f"{API_URL}/analytics/top-items", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching top items: {str(e)}")
        return []

def fetch_sales_by_time(time_unit: str = "day", date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> List[Dict]:
    """Fetch sales by time unit from API"""
    params = {'time_unit': time_unit}
    if date_from:
        params['date_from'] = date_from.isoformat()
    if date_to:
        params['date_to'] = date_to.isoformat()
    
    try:
        response = requests.get(f"{API_URL}/analytics/sales-by-time", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching sales by time: {str(e)}")
        return []

def fetch_orders(
    date_from: Optional[datetime] = None, 
    date_to: Optional[datetime] = None,
    mode_of_order: Optional[str] = None,
    payment_mode: Optional[str] = None,
    time_of_day: Optional[str] = None,
    item_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Dict]:
    """Fetch orders with filters from API"""
    params = {'skip': skip, 'limit': limit}
    
    if date_from:
        params['date_from'] = date_from.isoformat()
    if date_to:
        params['date_to'] = date_to.isoformat()
    if mode_of_order:
        params['mode_of_order'] = mode_of_order
    if payment_mode:
        params['payment_mode'] = payment_mode
    if time_of_day:
        params['time_of_day'] = time_of_day
    if item_id:
        params['item_id'] = item_id
    
    try:
        response = requests.get(f"{API_URL}/orders/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching orders: {str(e)}")
        return []

def render_kpi_card(title: str, value: str, delta: Optional[str] = None, delta_color: str = "normal"):
    """Render a KPI card with title and value"""
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )

def render_analysis():
    st.header("Sales Analysis")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.now().date()
        start_date = st.date_input(
            "Start Date",
            value=today - timedelta(days=30),
            max_value=today
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=today,
            max_value=today,
            min_value=start_date
        )
    
    # Convert to datetime
    date_from = datetime.combine(start_date, datetime.min.time())
    date_to = datetime.combine(end_date, datetime.max.time())
    
    # Time of day filter
    time_of_day = st.multiselect(
        "Time of Day",
        options=["morning", "afternoon", "evening", "night"],
        default=[]
    )
    
    # Payment mode filter
    payment_mode = st.multiselect(
        "Payment Mode",
        options=["cash", "card", "upi", "wallet"],
        default=[]
    )
    
    # Fetch analytics data
    summary = fetch_analytics_summary(date_from, date_to)
    top_items = fetch_top_items(10, date_from, date_to)
    sales_by_day = fetch_sales_by_time("day", date_from, date_to)
    sales_by_hour = fetch_sales_by_time("hour", date_from, date_to)
    
    # KPI row
    st.subheader("Key Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        render_kpi_card(
            "Orders",
            f"{summary['total_orders']}"
        )
    
    with col2:
        render_kpi_card(
            "Total Sales",
            f"₹{float(summary['total_sales']):,.2f}"
        )
    
    with col3:
        render_kpi_card(
            "Making Cost",
            f"₹{float(summary['total_making_cost']):,.2f}"
        )
    
    with col4:
        render_kpi_card(
            "Total Profit",
            f"₹{float(summary['total_profit']):,.2f}",
            delta=f"{float(summary['total_profit']) / float(summary['total_sales']) * 100:.1f}%" if float(summary['total_sales']) > 0 else None
        )
    
    with col5:
        render_kpi_card(
            "Avg Order",
            f"₹{float(summary['average_order_value']):,.2f}"
        )
    
    # Charts
    st.subheader("Sales Analysis")
    
    # Create tabs for different charts
    tab1, tab2, tab3 = st.tabs(["Top Items", "Sales Trend", "Sales by Hour"])
    
    # Tab 1: Top Items
    with tab1:
        if top_items:
            # Convert to DataFrame
            df_top = pd.DataFrame(top_items)
            
            # Create bar chart
            fig = px.bar(
                df_top,
                x="item_name",
                y="total_sales",
                color="category",
                text="total_qty",
                title="Top Selling Items",
                labels={
                    "item_name": "Item",
                    "total_sales": "Sales (₹)",
                    "category": "Category",
                    "total_qty": "Quantity Sold"
                }
            )
            
            fig.update_layout(
                xaxis_tickangle=-45,
                yaxis_title="Sales (₹)",
                xaxis_title="",
                legend_title="Category",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sales data available for the selected period")
    
    # Tab 2: Sales Trend
    with tab2:
        if sales_by_day:
            # Convert to DataFrame
            df_trend = pd.DataFrame(sales_by_day)
            df_trend['time_unit'] = pd.to_datetime(df_trend['time_unit'])
            df_trend = df_trend.sort_values('time_unit')
            
            # Create line chart
            fig = px.line(
                df_trend,
                x="time_unit",
                y="sales",
                markers=True,
                title="Daily Sales Trend",
                labels={
                    "time_unit": "Date",
                    "sales": "Sales (₹)"
                }
            )
            
            # Add order count as a secondary axis
            fig.add_trace(
                go.Scatter(
                    x=df_trend['time_unit'],
                    y=df_trend['orders_count'],
                    mode='lines+markers',
                    name='Orders Count',
                    yaxis='y2'
                )
            )
            
            fig.update_layout(
                yaxis_title="Sales (₹)",
                xaxis_title="",
                yaxis2=dict(
                    title="Orders Count",
                    overlaying="y",
                    side="right"
                ),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display daily sales table
            st.subheader("Daily Sales Breakdown")
            daily_sales_df = df_trend.copy()
            daily_sales_df['Date'] = daily_sales_df['time_unit'].dt.strftime('%Y-%m-%d')
            daily_sales_df['Sales (₹)'] = daily_sales_df['sales'].apply(lambda x: f"₹{float(x):,.2f}")
            daily_sales_df['Orders'] = daily_sales_df['orders_count']
            display_df = daily_sales_df[['Date', 'Sales (₹)', 'Orders']]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Export to CSV
            csv = daily_sales_df[['Date', 'sales', 'orders_count']].to_csv(index=False)
            csv = csv.replace('sales', 'Sales (₹)').replace('orders_count', 'Orders')
            st.download_button(
                label="Export Daily Sales to CSV",
                data=csv,
                file_name=f"daily_sales_{start_date}_{end_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No sales data available for the selected period")
    
    # Tab 3: Sales by Hour
    with tab3:
        if sales_by_hour:
            # Convert to DataFrame
            df_hour = pd.DataFrame(sales_by_hour)
            
            # Extract hour from time_unit (format: HH:00)
            df_hour['hour'] = df_hour['time_unit'].str.split(':').str[0].astype(int)
            df_hour = df_hour.sort_values('hour')
            
            # Create bar chart
            fig = px.bar(
                df_hour,
                x="hour",
                y="sales",
                title="Sales by Hour of Day",
                labels={
                    "hour": "Hour of Day",
                    "sales": "Sales (₹)"
                }
            )
            
            # Add order count as a line
            fig.add_trace(
                go.Scatter(
                    x=df_hour['hour'],
                    y=df_hour['orders_count'],
                    mode='lines+markers',
                    name='Orders Count',
                    yaxis='y2'
                )
            )
            
            fig.update_layout(
                yaxis_title="Sales (₹)",
                xaxis_title="Hour of Day",
                xaxis=dict(
                    tickmode='array',
                    tickvals=list(range(24)),
                    ticktext=[f"{h:02d}:00" for h in range(24)]
                ),
                yaxis2=dict(
                    title="Orders Count",
                    overlaying="y",
                    side="right"
                ),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hourly sales data available for the selected period")
    
    # Orders table
    st.subheader("Orders")
    
    # Fetch orders with filters
    filters = {}
    if time_of_day:
        filters['time_of_day'] = time_of_day[0] if len(time_of_day) == 1 else None
    if payment_mode:
        filters['payment_mode'] = payment_mode[0] if len(payment_mode) == 1 else None
    
    orders = fetch_orders(date_from, date_to, **filters)
    
    if orders:
        # Convert to DataFrame
        df_orders = pd.DataFrame(orders)
        
        # Format timestamp
        df_orders['timestamp'] = pd.to_datetime(df_orders['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Format columns for display
        display_df = df_orders[['order_number', 'timestamp', 'customer_name', 'total_amount', 'payment_mode']]
        display_df = display_df.rename(columns={
            'order_number': 'Order #',
            'timestamp': 'Date & Time',
            'customer_name': 'Customer',
            'total_amount': 'Amount',
            'payment_mode': 'Payment'
        })
        
        # Format amount as currency
        display_df['Amount'] = display_df['Amount'].apply(lambda x: f"₹{float(x):,.2f}")
        
        # Display as table
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Export to CSV
        csv = df_orders.to_csv(index=False)
        st.download_button(
            label="Export to CSV",
            data=csv,
            file_name=f"orders_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.info("No orders found for the selected filters")


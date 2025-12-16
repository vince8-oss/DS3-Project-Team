"""
Brazilian Sales Economic Impact Dashboard - English Version
Interactive visualization with translated category names
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from datetime import datetime
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
# In dev mode, dbt creates schemas as {dataset}_marts
# So if BQ_DATASET_RAW is brazilian_sales, marts tables are in brazilian_sales_marts
BQ_DATASET_RAW = os.getenv('BQ_DATASET_RAW', 'brazilian_sales')
BQ_DATASET_MARTS = f"{BQ_DATASET_RAW}_marts"
CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Page configuration
st.set_page_config(
    page_title="Brazilian Sales Economic Analysis",
    page_icon="📊",
    layout="wide"
)

# Initialize BigQuery client
@st.cache_resource
def get_bigquery_client():
    """Initialize BigQuery client"""
    if not CREDENTIALS_PATH:
        st.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        return None
    return bigquery.Client.from_service_account_json(CREDENTIALS_PATH)

# Load data with caching
@st.cache_data(ttl=3600)
def load_category_data():
    """Load category performance data with English names"""
    client = get_bigquery_client()
    query = f"""
    SELECT
        category_name,
        category_name_pt,
        order_month,
        customer_state,
        order_count,
        total_revenue_brl,
        total_revenue_usd,
        avg_order_value_brl,
        avg_exchange_rate,
        exchange_rate_period
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_MARTS}.fct_category_performance_economics`
    WHERE category_name IS NOT NULL
    ORDER BY order_month DESC
    """
    df = client.query(query).to_dataframe()
    # Convert order_month to datetime
    df['order_month'] = pd.to_datetime(df['order_month'])
    return df

@st.cache_data(ttl=3600)
def load_geographic_data():
    """Load geographic sales data with English names"""
    client = get_bigquery_client()
    query = f"""
    SELECT
        customer_state,
        customer_city,
        order_month,
        category_name,
        category_name_pt,
        order_count,
        total_revenue_brl,
        total_revenue_usd,
        avg_exchange_rate,
        currency_strength
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_MARTS}.fct_geographic_sales_economics`
    WHERE category_name IS NOT NULL
    ORDER BY order_month DESC
    """
    df = client.query(query).to_dataframe()
    # Convert order_month to datetime
    df['order_month'] = pd.to_datetime(df['order_month'])
    return df

@st.cache_data(ttl=3600)
def load_time_series_data():
    """Load daily time series data"""
    client = get_bigquery_client()
    query = f"""
    SELECT
        order_date,
        daily_orders,
        daily_customers,
        daily_revenue_usd,
        avg_order_value_usd,
        avg_exchange_rate,
        inflation_rate,
        interest_rate,
        order_year,
        order_month,
        order_quarter,
        day_of_week,
        day_name,
        month_name
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_MARTS}.fct_time_series_daily`
    ORDER BY order_date
    """
    try:
        df = client.query(query).to_dataframe()
        df['order_date'] = pd.to_datetime(df['order_date'])
        return df
    except Exception as e:
        st.warning(f"Time series data not available yet. Build the mart with: dbt run --select fct_time_series_daily")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_product_performance():
    """Load product performance data"""
    client = get_bigquery_client()
    query = f"""
    SELECT
        product_id,
        category_name,
        category_name_pt,
        total_orders,
        total_revenue_usd,
        avg_price_usd,
        total_freight_brl,
        avg_freight_percentage,
        rank_in_category,
        overall_rank,
        first_order_date,
        last_order_date,
        states_sold_to
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_MARTS}.fct_product_performance`
    WHERE overall_rank <= 100
    ORDER BY total_revenue_usd DESC
    """
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.warning(f"Product performance data not available yet. Build the mart with: dbt run --select fct_product_performance")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_customer_segments():
    """Load customer segmentation data"""
    client = get_bigquery_client()
    query = f"""
    SELECT
        customer_unique_id,
        customer_state,
        total_orders,
        total_spent_usd,
        avg_order_value_usd,
        recency_score,
        frequency_score,
        monetary_score,
        rfm_score,
        rfm_segment,
        customer_type,
        customer_status,
        value_tier,
        annualized_clv_usd,
        days_since_last_order
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_MARTS}.fct_customer_segments`
    ORDER BY total_spent_usd DESC
    LIMIT 10000
    """
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.warning(f"Customer segments data not available yet. Build the mart with: dbt run --select fct_customer_segments")
        return pd.DataFrame()

# Main app
def main():
    st.title("🇧🇷 Brazilian E-commerce Economic Impact Dashboard")
    st.markdown("### Analyze how exchange rates, inflation, and interest rates affect sales")
    
    # Language toggle in sidebar
    st.sidebar.header("🔍 Filters")
    
    show_language = st.sidebar.radio(
        "Category Names Language",
        options=["English", "Portuguese", "Both"],
        index=0
    )
    
    # Load data
    with st.spinner("Loading data..."):
        df_category = load_category_data()
        df_geo = load_geographic_data()
        df_time_series = load_time_series_data()
        df_products = load_product_performance()
        df_customers = load_customer_segments()
    
    # Add display column based on language preference
    if show_language == "English":
        df_category['display_category'] = df_category['category_name']
        df_geo['display_category'] = df_geo['category_name']
    elif show_language == "Portuguese":
        df_category['display_category'] = df_category['category_name_pt']
        df_geo['display_category'] = df_geo['category_name_pt']
    else:  # Both
        df_category['display_category'] = df_category['category_name'] + ' (' + df_category['category_name_pt'] + ')'
        df_geo['display_category'] = df_geo['category_name'] + ' (' + df_geo['category_name_pt'] + ')'
    
    # Date range filter
    if not df_category.empty:
        min_date = df_category['order_month'].min()
        max_date = df_category['order_month'].max()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Apply date filter
        if len(date_range) == 2:
            df_category = df_category[
                (df_category['order_month'] >= pd.Timestamp(date_range[0])) &
                (df_category['order_month'] <= pd.Timestamp(date_range[1]))
            ]
            df_geo = df_geo[
                (df_geo['order_month'] >= pd.Timestamp(date_range[0])) &
                (df_geo['order_month'] <= pd.Timestamp(date_range[1]))
            ]
    
    # Product category filter (using English names for selection)
    categories = sorted(df_category['category_name'].unique())
    selected_categories = st.sidebar.multiselect(
        "Product Categories",
        options=categories,
        default=categories[:5] if len(categories) > 5 else categories
    )
    
    # State filter
    states = sorted(df_geo['customer_state'].unique())
    selected_states = st.sidebar.multiselect(
        "States",
        options=states,
        default=states[:5] if len(states) > 5 else states
    )
    
    # Economic period filter
    exchange_periods = df_category['exchange_rate_period'].unique()
    selected_exchange = st.sidebar.multiselect(
        "Exchange Rate Period",
        options=exchange_periods,
        default=list(exchange_periods)
    )
    
    # Apply filters
    df_cat_filtered = df_category[
        (df_category['category_name'].isin(selected_categories)) &
        (df_category['exchange_rate_period'].isin(selected_exchange))
    ]
    
    df_geo_filtered = df_geo[
        (df_geo['customer_state'].isin(selected_states)) &
        (df_geo['category_name'].isin(selected_categories))
    ]
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 Overview",
        "📊 Time Series",
        "🏷️ Category Analysis",
        "🛍️ Product Performance",
        "👥 Customer Analytics",
        "🗺️ Geographic Analysis",
        "💱 Economic Impact"
    ])
    
    # TAB 1: Overview
    with tab1:
        st.header("Key Metrics Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_orders = df_cat_filtered['order_count'].sum()
            st.metric("Total Orders", f"{total_orders:,.0f}")
        
        with col2:
            total_revenue = df_cat_filtered['total_revenue_usd'].sum()
            st.metric("Total Revenue (USD)", f"${total_revenue:,.0f}")
        
        with col3:
            avg_exchange = df_cat_filtered['avg_exchange_rate'].mean()
            st.metric("Avg Exchange Rate", f"{avg_exchange:.2f} BRL/USD")
        
        with col4:
            categories_count = len(selected_categories)
            st.metric("Categories Analyzed", categories_count)
        
        # Revenue trend over time
        st.subheader("📊 Monthly Revenue Trend")
        monthly_revenue = df_cat_filtered.groupby('order_month').agg({
            'total_revenue_usd': 'sum',
            'order_count': 'sum',
            'avg_exchange_rate': 'mean'
        }).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_revenue['order_month'],
            y=monthly_revenue['total_revenue_usd'],
            mode='lines+markers',
            name='Revenue (USD)',
            line=dict(color='#1f77b4', width=3)
        ))
        fig.update_layout(
            title="Monthly Revenue Trend (USD)",
            xaxis_title="Month",
            yaxis_title="Revenue (USD)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Exchange rate overlay
        st.subheader("💱 Revenue vs Exchange Rate")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=monthly_revenue['order_month'],
            y=monthly_revenue['total_revenue_usd'],
            mode='lines+markers',
            name='Revenue USD',
            yaxis='y1'
        ))
        fig2.add_trace(go.Scatter(
            x=monthly_revenue['order_month'],
            y=monthly_revenue['avg_exchange_rate'],
            mode='lines+markers',
            name='USD/BRL Rate',
            yaxis='y2',
            line=dict(color='red')
        ))
        fig2.update_layout(
            title="Revenue and Exchange Rate Over Time",
            xaxis_title="Month",
            yaxis=dict(title="Revenue (USD)"),
            yaxis2=dict(title="Exchange Rate (BRL/USD)", overlaying='y', side='right'),
            height=400
        )
        st.plotly_chart(fig2, use_container_width=True)

    # TAB 2: Time Series Analysis
    with tab2:
        st.header("📊 Time Series Analysis")

        if not df_time_series.empty:
            # Multi-timeframe selector
            timeframe = st.selectbox(
                "Select Time Aggregation",
                options=["Daily", "Weekly", "Monthly", "Quarterly"],
                index=2
            )

            # Aggregate data based on selected timeframe
            if timeframe == "Daily":
                ts_data = df_time_series.copy()
                date_col = 'order_date'
            elif timeframe == "Weekly":
                ts_data = df_time_series.groupby(pd.Grouper(key='order_date', freq='W')).agg({
                    'daily_orders': 'sum',
                    'daily_revenue_usd': 'sum',
                    'avg_order_value_usd': 'mean',
                    'avg_exchange_rate': 'mean'
                }).reset_index()
                date_col = 'order_date'
            elif timeframe == "Monthly":
                ts_data = df_time_series.groupby(['order_year', 'order_month']).agg({
                    'daily_orders': 'sum',
                    'daily_revenue_usd': 'sum',
                    'avg_order_value_usd': 'mean',
                    'avg_exchange_rate': 'mean',
                    'order_date': 'first'
                }).reset_index()
                date_col = 'order_date'
            else:  # Quarterly
                ts_data = df_time_series.groupby(['order_year', 'order_quarter']).agg({
                    'daily_orders': 'sum',
                    'daily_revenue_usd': 'sum',
                    'avg_order_value_usd': 'mean',
                    'avg_exchange_rate': 'mean',
                    'order_date': 'first'
                }).reset_index()
                date_col = 'order_date'

            # Revenue Trend
            st.subheader(f"{timeframe} Revenue Trend")
            fig = px.line(
                ts_data,
                x=date_col,
                y='daily_revenue_usd',
                title=f"{timeframe} Revenue (USD)",
                markers=True
            )
            fig.update_layout(xaxis_title="Date", yaxis_title="Revenue (USD)", height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Order Volume vs Revenue (Dual-axis)
            st.subheader("📦 Order Volume vs Revenue")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts_data[date_col],
                y=ts_data['daily_revenue_usd'],
                mode='lines+markers',
                name='Revenue (USD)',
                yaxis='y1',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=ts_data[date_col],
                y=ts_data['daily_orders'],
                mode='lines+markers',
                name='Order Count',
                yaxis='y2',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig.update_layout(
                title="Revenue vs Order Volume Over Time",
                xaxis_title="Date",
                yaxis=dict(title="Revenue (USD)", side='left'),
                yaxis2=dict(title="Order Count", overlaying='y', side='right'),
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Year-over-Year Comparison
            if 'order_year' in ts_data.columns and len(ts_data['order_year'].unique()) > 1:
                st.subheader("📅 Year-over-Year Comparison")

                # Group by month and year
                yoy_data = df_time_series.groupby(['order_year', 'order_month']).agg({
                    'daily_revenue_usd': 'sum'
                }).reset_index()
                yoy_data['order_year'] = yoy_data['order_year'].astype(str)

                fig = px.line(
                    yoy_data,
                    x='order_month',
                    y='daily_revenue_usd',
                    color='order_year',
                    title="Monthly Revenue Comparison by Year",
                    markers=True
                )
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Revenue (USD)",
                    height=400,
                    xaxis=dict(tickmode='linear', tick0=1, dtick=1)
                )
                st.plotly_chart(fig, use_container_width=True)

            # Seasonality Analysis
            st.subheader("🌊 Seasonality Patterns")
            col1, col2 = st.columns(2)

            with col1:
                # Day of week pattern
                dow_pattern = df_time_series.groupby('day_name').agg({
                    'daily_revenue_usd': 'mean',
                    'daily_orders': 'mean'
                }).reset_index()
                # Order days correctly
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                dow_pattern['day_name'] = pd.Categorical(dow_pattern['day_name'], categories=day_order, ordered=True)
                dow_pattern = dow_pattern.sort_values('day_name')

                fig = px.bar(
                    dow_pattern,
                    x='day_name',
                    y='daily_revenue_usd',
                    title="Average Revenue by Day of Week",
                    labels={'daily_revenue_usd': 'Avg Revenue (USD)', 'day_name': 'Day'}
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Monthly pattern
                monthly_pattern = df_time_series.groupby('month_name').agg({
                    'daily_revenue_usd': 'mean',
                    'daily_orders': 'mean'
                }).reset_index()

                fig = px.bar(
                    monthly_pattern,
                    x='month_name',
                    y='daily_revenue_usd',
                    title="Average Revenue by Month",
                    labels={'daily_revenue_usd': 'Avg Revenue (USD)', 'month_name': 'Month'}
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Time series data not available. Build the mart first: `dbt run --select fct_time_series_daily`")

    # TAB 3: Category Analysis
    with tab3:
        st.header("🏷️ Product Category Performance")
        
        # Category performance by exchange rate period
        st.subheader("Category Performance by Economic Period")
        
        category_comparison = df_cat_filtered.groupby(
            ['display_category', 'exchange_rate_period']
        ).agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum'
        }).reset_index()
        
        fig = px.bar(
            category_comparison,
            x='display_category',
            y='total_revenue_usd',
            color='exchange_rate_period',
            title="Revenue by Category and Exchange Rate Period",
            labels={'total_revenue_usd': 'Revenue (USD)', 'display_category': 'Category'},
            barmode='group',
            height=500
        )
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Top categories
        st.subheader("📊 Top Performing Categories")
        top_categories = df_cat_filtered.groupby('display_category').agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum',
            'avg_exchange_rate': 'mean'
        }).reset_index().sort_values('total_revenue_usd', ascending=False).head(10)
        
        fig = px.bar(
            top_categories,
            x='total_revenue_usd',
            y='display_category',
            orientation='h',
            title="Top 10 Categories by Revenue",
            labels={'total_revenue_usd': 'Revenue (USD)', 'display_category': 'Category'},
            color='total_revenue_usd',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Category trend
        st.subheader("📈 Category Trend Over Time")
        selected_cat_trend = st.selectbox(
            "Select category to view trend",
            options=sorted(df_cat_filtered['display_category'].unique())
        )
        
        cat_trend = df_cat_filtered[
            df_cat_filtered['display_category'] == selected_cat_trend
        ].groupby('order_month').agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum'
        }).reset_index()
        
        fig = px.line(
            cat_trend,
            x='order_month',
            y='total_revenue_usd',
            title=f"Revenue Trend: {selected_cat_trend}",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

    # TAB 4: Product Performance
    with tab4:
        st.header("🛍️ Product Performance Analysis")

        if not df_products.empty:
            # Add display column for products
            if show_language == "English":
                df_products['display_category'] = df_products['category_name']
            elif show_language == "Portuguese":
                df_products['display_category'] = df_products['category_name_pt']
            else:
                df_products['display_category'] = df_products['category_name'] + ' (' + df_products['category_name_pt'] + ')'

            # Top Products Overall
            st.subheader("🏆 Top 20 Products by Revenue")

            top_20 = df_products.head(20)
            fig = px.bar(
                top_20,
                x='total_revenue_usd',
                y='product_id',
                orientation='h',
                color='display_category',
                title="Top 20 Products by Revenue (USD)",
                labels={'total_revenue_usd': 'Revenue (USD)', 'product_id': 'Product ID'},
                hover_data=['total_orders', 'avg_price_usd', 'states_sold_to']
            )
            fig.update_layout(height=600, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

            # Product Performance Matrix
            st.subheader("📊 Product Performance Matrix")
            st.markdown("*Bubble size represents average price*")

            fig = px.scatter(
                df_products.head(50),
                x='total_orders',
                y='total_revenue_usd',
                size='avg_price_usd',
                color='display_category',
                hover_data=['product_id', 'states_sold_to'],
                title="Revenue vs Order Count (Top 50 Products)",
                labels={
                    'total_orders': 'Total Orders',
                    'total_revenue_usd': 'Revenue (USD)',
                    'display_category': 'Category'
                }
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

            # Top Products by Category
            st.subheader("🏷️ Top Products per Category")

            if 'display_category' in df_products.columns and len(df_products['display_category'].unique()) > 0:
                selected_prod_category = st.selectbox(
                    "Select Category",
                    options=sorted(df_products['display_category'].unique()),
                    key="product_category_selector"
                )

                category_products = df_products[df_products['display_category'] == selected_prod_category].head(10)

                if not category_products.empty:
                    fig = px.bar(
                        category_products,
                        x='total_revenue_usd',
                        y='product_id',
                        orientation='h',
                        title=f"Top 10 Products in {selected_prod_category}",
                        labels={'total_revenue_usd': 'Revenue (USD)', 'product_id': 'Product ID'},
                        hover_data=['total_orders', 'avg_price_usd'],
                        color='total_revenue_usd',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Product details table
                    st.subheader("Product Details")
                    display_cols = ['product_id', 'total_orders', 'total_revenue_usd', 'avg_price_usd',
                                   'avg_freight_percentage', 'states_sold_to']
                    st.dataframe(category_products[display_cols], use_container_width=True)
            else:
                st.info("No product categories available to display.")
        else:
            st.info("Product data not available. Build the mart first: `dbt run --select fct_product_performance`")

    # TAB 5: Customer Analytics
    with tab5:
        st.header("👥 Customer Analytics")

        if not df_customers.empty:
            # Key Metrics
            st.subheader("📊 Customer Overview")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_customers = len(df_customers)
                st.metric("Total Customers", f"{total_customers:,}")

            with col2:
                repeat_customers = len(df_customers[df_customers['total_orders'] > 1])
                repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
                st.metric("Repeat Purchase Rate", f"{repeat_rate:.1f}%")

            with col3:
                avg_clv = df_customers['annualized_clv_usd'].mean()
                st.metric("Avg Customer LTV (Annual)", f"${avg_clv:.0f}")

            with col4:
                avg_orders = df_customers['total_orders'].mean()
                st.metric("Avg Orders per Customer", f"{avg_orders:.1f}")

            # RFM Segmentation
            st.subheader("🎯 RFM Customer Segments")

            segment_counts = df_customers.groupby('rfm_segment').agg({
                'customer_unique_id': 'count',
                'total_spent_usd': 'sum',
                'total_orders': 'sum'
            }).reset_index()
            segment_counts.columns = ['RFM Segment', 'Customer Count', 'Total Revenue', 'Total Orders']
            segment_counts = segment_counts.sort_values('Total Revenue', ascending=False)

            col1, col2 = st.columns(2)

            with col1:
                fig = px.pie(
                    segment_counts,
                    values='Customer Count',
                    names='RFM Segment',
                    title="Customer Distribution by RFM Segment"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(
                    segment_counts,
                    x='RFM Segment',
                    y='Total Revenue',
                    title="Revenue by RFM Segment",
                    color='Total Revenue',
                    color_continuous_scale='Blues'
                )
                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # Customer Type Distribution
            st.subheader("👤 Customer Type Distribution")

            type_counts = df_customers.groupby('customer_type').agg({
                'customer_unique_id': 'count',
                'total_spent_usd': 'sum'
            }).reset_index()
            type_counts.columns = ['Customer Type', 'Count', 'Total Spent']

            col1, col2 = st.columns(2)

            with col1:
                fig = px.bar(
                    type_counts,
                    x='Customer Type',
                    y='Count',
                    title="Customer Count by Type",
                    color='Customer Type'
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(
                    type_counts,
                    x='Customer Type',
                    y='Total Spent',
                    title="Revenue by Customer Type",
                    color='Customer Type'
                )
                st.plotly_chart(fig, use_container_width=True)

            # Customer Status Analysis
            st.subheader("📈 Customer Status & Churn Risk")

            status_counts = df_customers.groupby('customer_status').agg({
                'customer_unique_id': 'count',
                'total_spent_usd': 'sum'
            }).reset_index()
            status_counts.columns = ['Status', 'Count', 'Total Revenue']

            fig = px.bar(
                status_counts,
                x='Status',
                y='Count',
                title="Customers by Status (Active/At Risk/Dormant/Churned)",
                color='Status',
                color_discrete_map={
                    'Active': 'green',
                    'At Risk': 'orange',
                    'Dormant': 'red',
                    'Churned': 'darkred'
                }
            )
            st.plotly_chart(fig, use_container_width=True)

            # Value Tier Analysis
            st.subheader("💎 Customer Value Tiers")

            value_tier_stats = df_customers.groupby('value_tier').agg({
                'customer_unique_id': 'count',
                'total_spent_usd': 'sum',
                'annualized_clv_usd': 'mean'
            }).reset_index()
            value_tier_stats.columns = ['Value Tier', 'Customers', 'Total Revenue', 'Avg CLV']

            st.dataframe(value_tier_stats.style.format({
                'Total Revenue': '${:,.0f}',
                'Avg CLV': '${:,.0f}'
            }), use_container_width=True)

            # RFM Score Distribution (3D Scatter)
            st.subheader("🎲 RFM Score Distribution")

            fig = px.scatter_3d(
                df_customers.head(500),
                x='recency_score',
                y='frequency_score',
                z='monetary_score',
                color='rfm_segment',
                hover_data=['customer_state', 'total_orders', 'total_spent_usd'],
                title="RFM 3D Scatter (Sample of 500 customers)",
                labels={
                    'recency_score': 'Recency',
                    'frequency_score': 'Frequency',
                    'monetary_score': 'Monetary'
                }
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Customer segments data not available. Build the mart first: `dbt run --select fct_customer_segments`")

    # TAB 6: Geographic Analysis
    with tab6:
        st.header("🗺️ Geographic Sales Analysis")
        
        # Sales by state
        st.subheader("Sales by State")
        state_sales = df_geo_filtered.groupby('customer_state').agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum'
        }).reset_index().sort_values('total_revenue_usd', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                state_sales,
                x='customer_state',
                y='total_revenue_usd',
                title="Revenue by State",
                labels={'total_revenue_usd': 'Revenue (USD)', 'customer_state': 'State'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                state_sales.head(10),
                values='order_count',
                names='customer_state',
                title="Order Distribution (Top 10 States)"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Interactive Choropleth Map
        st.subheader("🗺️ Interactive State Revenue Map")

        # Brazil state codes mapping
        brazil_states = {
            'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
            'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
            'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
            'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
            'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
            'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima',
            'SC': 'Santa Catarina', 'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
        }

        # Prepare data for choropleth
        map_data = state_sales.copy()
        map_data['state_name'] = map_data['customer_state'].map(brazil_states)

        # Create choropleth map
        fig = px.choropleth(
            map_data,
            locations='customer_state',
            locationmode='geojson-id',
            color='total_revenue_usd',
            hover_name='state_name',
            hover_data={
                'customer_state': False,
                'total_revenue_usd': ':$,.0f',
                'order_count': ':,',
            },
            labels={
                'total_revenue_usd': 'Revenue (USD)',
                'order_count': 'Orders'
            },
            title="Revenue Distribution Across Brazilian States",
            color_continuous_scale='Blues',
            scope='south america'
        )

        fig.update_geos(
            visible=False,
            resolution=50,
            showcountries=True,
            countrycolor="lightgray",
            fitbounds="locations"
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

        # Geographic Concentration Metrics
        st.subheader("📊 Geographic Concentration Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Top 5 concentration
            top5_revenue = state_sales.head(5)['total_revenue_usd'].sum()
            total_revenue = state_sales['total_revenue_usd'].sum()
            top5_pct = (top5_revenue / total_revenue * 100) if total_revenue > 0 else 0
            st.metric("Top 5 States Revenue %", f"{top5_pct:.1f}%")

        with col2:
            # Herfindahl-Hirschman Index (HHI)
            state_sales['market_share'] = state_sales['total_revenue_usd'] / state_sales['total_revenue_usd'].sum()
            hhi = (state_sales['market_share'] ** 2).sum() * 10000
            st.metric("HHI (Concentration Index)", f"{hhi:.0f}")
            st.caption("HHI < 1500: Competitive, 1500-2500: Moderate, >2500: Concentrated")

        with col3:
            # Number of active states
            active_states = len(state_sales)
            st.metric("Active States", f"{active_states}")

        # Geographic heatmap
        st.subheader("🗺️ State Performance Heatmap")
        
        state_category = df_geo_filtered.groupby(
            ['customer_state', 'display_category']
        ).agg({
            'order_count': 'sum'
        }).reset_index()
        
        # Pivot for heatmap
        heatmap_data = state_category.pivot(
            index='customer_state',
            columns='display_category',
            values='order_count'
        ).fillna(0)
        
        fig = px.imshow(
            heatmap_data,
            title="Order Volume by State and Category",
            labels=dict(x="Category", y="State", color="Orders"),
            color_continuous_scale='Blues',
            aspect='auto'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top cities
        st.subheader("🏙️ Top Cities by Revenue")
        city_sales = df_geo_filtered.groupby(['customer_state', 'customer_city']).agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum'
        }).reset_index().sort_values('total_revenue_usd', ascending=False).head(15)
        
        city_sales['city_state'] = city_sales['customer_city'] + ', ' + city_sales['customer_state']
        
        fig = px.bar(
            city_sales,
            x='total_revenue_usd',
            y='city_state',
            orientation='h',
            title="Top 15 Cities by Revenue",
            labels={'total_revenue_usd': 'Revenue (USD)', 'city_state': 'City'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # TAB 7: Economic Impact
    with tab7:
        st.header("💱 Economic Indicators Impact")

        # Enhanced Correlation Analysis with all 3 indicators
        if not df_time_series.empty:
            st.subheader("📊 Correlation Analysis: Sales vs Economic Indicators")

            # Prepare correlation data
            corr_data = df_time_series[['daily_revenue_usd', 'daily_orders', 'avg_exchange_rate',
                                        'inflation_rate', 'interest_rate']].dropna()

            if not corr_data.empty:
                # Correlation matrix
                correlation_matrix = corr_data.corr()

                # Display correlation heatmap
                fig = px.imshow(
                    correlation_matrix,
                    title="Correlation Matrix: Sales & Economic Indicators",
                    labels=dict(color="Correlation"),
                    color_continuous_scale='RdBu_r',
                    zmin=-1,
                    zmax=1,
                    text_auto='.2f',
                    aspect='auto'
                )
                st.plotly_chart(fig, use_container_width=True)

                # Scatter plots for each indicator
                st.subheader("Detailed Relationships")

                col1, col2, col3 = st.columns(3)

                with col1:
                    # Revenue vs Exchange Rate
                    fig = px.scatter(
                        corr_data,
                        x='avg_exchange_rate',
                        y='daily_revenue_usd',
                        trendline='ols',
                        title="Revenue vs Exchange Rate",
                        labels={
                            'avg_exchange_rate': 'USD/BRL Exchange Rate',
                            'daily_revenue_usd': 'Daily Revenue (USD)'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Correlation coefficient
                    corr_val = correlation_matrix.loc['daily_revenue_usd', 'avg_exchange_rate']
                    st.metric("Correlation", f"{corr_val:.3f}")

                with col2:
                    # Revenue vs Inflation (IPCA)
                    fig = px.scatter(
                        corr_data,
                        x='inflation_rate',
                        y='daily_revenue_usd',
                        trendline='ols',
                        title="Revenue vs Inflation (IPCA)",
                        labels={
                            'inflation_rate': 'IPCA (%)',
                            'daily_revenue_usd': 'Daily Revenue (USD)'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    corr_val = correlation_matrix.loc['daily_revenue_usd', 'inflation_rate']
                    st.metric("Correlation", f"{corr_val:.3f}")

                with col3:
                    # Revenue vs Interest Rate (SELIC)
                    fig = px.scatter(
                        corr_data,
                        x='interest_rate',
                        y='daily_revenue_usd',
                        trendline='ols',
                        title="Revenue vs Interest Rate (SELIC)",
                        labels={
                            'interest_rate': 'SELIC Rate (%)',
                            'daily_revenue_usd': 'Daily Revenue (USD)'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    corr_val = correlation_matrix.loc['daily_revenue_usd', 'interest_rate']
                    st.metric("Correlation", f"{corr_val:.3f}")

                # Time series of all indicators together
                st.subheader("Economic Indicators Over Time")

                fig = go.Figure()

                # Normalize values for comparison (0-100 scale)
                def normalize(series):
                    return (series - series.min()) / (series.max() - series.min()) * 100 if series.max() > series.min() else series

                fig.add_trace(go.Scatter(
                    x=df_time_series['order_date'],
                    y=normalize(df_time_series['avg_exchange_rate']),
                    mode='lines',
                    name='Exchange Rate',
                    line=dict(color='blue')
                ))

                fig.add_trace(go.Scatter(
                    x=df_time_series['order_date'],
                    y=normalize(df_time_series['inflation_rate']),
                    mode='lines',
                    name='Inflation (IPCA)',
                    line=dict(color='red')
                ))

                fig.add_trace(go.Scatter(
                    x=df_time_series['order_date'],
                    y=normalize(df_time_series['interest_rate']),
                    mode='lines',
                    name='Interest Rate (SELIC)',
                    line=dict(color='green')
                ))

                fig.update_layout(
                    title="Normalized Economic Indicators Trends (0-100 Scale)",
                    xaxis_title="Date",
                    yaxis_title="Normalized Value",
                    height=400,
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)

        # Economic period comparison
        st.subheader("Performance by Economic Period")
        
        economic_summary = df_cat_filtered.groupby('exchange_rate_period').agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum',
            'avg_exchange_rate': 'mean'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                economic_summary,
                x='exchange_rate_period',
                y='order_count',
                title="Orders by Exchange Rate Period",
                color='exchange_rate_period'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                economic_summary,
                x='exchange_rate_period',
                y='total_revenue_usd',
                title="Revenue by Exchange Rate Period",
                color='exchange_rate_period'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Category elasticity
        st.subheader("📊 Category Economic Sensitivity")
        
        category_elasticity = df_cat_filtered.groupby(
            ['display_category', 'exchange_rate_period']
        ).agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum'
        }).reset_index()
        
        # Calculate variance
        category_variance = category_elasticity.pivot(
            index='display_category',
            columns='exchange_rate_period',
            values='order_count'
        ).fillna(0)
        
        if 'Strong BRL' in category_variance.columns and 'Weak BRL' in category_variance.columns:
            category_variance['elasticity'] = (
                100 * (category_variance['Weak BRL'] - category_variance['Strong BRL']) / 
                category_variance['Strong BRL'].replace(0, np.nan)
            ).fillna(0)
            
            elasticity_df = category_variance[['elasticity']].reset_index()
            elasticity_df = elasticity_df.sort_values('elasticity', ascending=False).head(15)
            
            fig = px.bar(
                elasticity_df,
                x='elasticity',
                y='display_category',
                orientation='h',
                title="Category Sensitivity to Exchange Rate (% Change)",
                labels={'elasticity': 'Change (%)', 'display_category': 'Category'},
                color='elasticity',
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("""
            **Interpretation:**
            - **Positive values**: Category sells MORE during weak BRL (import-sensitive or luxury)
            - **Negative values**: Category sells LESS during weak BRL (counter-cyclical)
            - **Near zero**: Stable category regardless of exchange rate
            """)
        
        # Raw data view
        st.subheader("📋 Detailed Data")
        if st.checkbox("Show raw data"):
            st.dataframe(df_cat_filtered.head(100))

if __name__ == "__main__":
    main()

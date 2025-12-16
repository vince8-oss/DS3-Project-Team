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
    categories = sorted([x for x in df_category['category_name'].unique() if x is not None and pd.notna(x)])
    selected_categories = st.sidebar.multiselect(
        "Product Categories",
        options=categories,
        default=categories[:5] if len(categories) > 5 else categories
    )

    # State filter
    states = sorted([x for x in df_geo['customer_state'].unique() if x is not None and pd.notna(x)])
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

        # Category Treemap
        st.subheader("🗂️ Category Revenue Distribution (Treemap)")

        category_totals = df_cat_filtered.groupby('display_category').agg({
            'total_revenue_usd': 'sum',
            'order_count': 'sum'
        }).reset_index()

        fig = px.treemap(
            category_totals,
            path=['display_category'],
            values='total_revenue_usd',
            title="Category Revenue Treemap",
            color='total_revenue_usd',
            color_continuous_scale='Blues',
            hover_data={
                'total_revenue_usd': ':$,.0f',
                'order_count': ':,',
            }
        )
        fig.update_traces(textinfo="label+value+percent parent")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Category Distribution Pie Chart
        col1, col2 = st.columns(2)

        with col1:
            # Revenue distribution
            fig = px.pie(
                category_totals.head(10),
                values='total_revenue_usd',
                names='display_category',
                title="Revenue Share (Top 10 Categories)",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Order count distribution
            fig = px.pie(
                category_totals.head(10),
                values='order_count',
                names='display_category',
                title="Order Count Share (Top 10 Categories)",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)

        # Category trend
        st.subheader("📈 Category Trend Over Time")
        selected_cat_trend = st.selectbox(
            "Select category to view trend",
            options=sorted([x for x in df_cat_filtered['display_category'].unique() if x is not None and pd.notna(x)])
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
                    options=sorted([x for x in df_products['display_category'].unique() if x is not None and pd.notna(x)]),
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

            # Freight Cost Analysis
            st.subheader("📦 Freight Cost Analysis")

            if 'avg_freight_percentage' in df_products.columns:
                # Top products by freight percentage
                high_freight_products = df_products.nlargest(20, 'avg_freight_percentage')

                col1, col2 = st.columns(2)

                with col1:
                    fig = px.bar(
                        high_freight_products,
                        x='avg_freight_percentage',
                        y='product_id',
                        orientation='h',
                        title="Top 20 Products by Freight % (of Price)",
                        labels={'avg_freight_percentage': 'Freight %', 'product_id': 'Product ID'},
                        color='avg_freight_percentage',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Freight % by category
                    freight_by_category = df_products.groupby('display_category').agg({
                        'avg_freight_percentage': 'mean',
                        'total_freight_brl': 'sum'
                    }).reset_index().sort_values('avg_freight_percentage', ascending=False).head(10)

                    fig = px.bar(
                        freight_by_category,
                        x='avg_freight_percentage',
                        y='display_category',
                        orientation='h',
                        title="Top 10 Categories by Avg Freight %",
                        labels={'avg_freight_percentage': 'Avg Freight %', 'display_category': 'Category'},
                        color='avg_freight_percentage',
                        color_continuous_scale='Oranges'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Freight impact analysis
                st.markdown("**Freight Impact Insights:**")
                avg_freight_pct = df_products['avg_freight_percentage'].mean()
                high_freight_categories = freight_by_category.head(3)['display_category'].tolist()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Avg Freight % of Price", f"{avg_freight_pct:.1f}%")
                with col2:
                    total_freight_cost = df_products['total_freight_brl'].sum()
                    st.metric("Total Freight Cost (BRL)", f"R${total_freight_cost:,.0f}")
                with col3:
                    high_freight_count = len(df_products[df_products['avg_freight_percentage'] > 20])
                    st.metric("Products with >20% Freight", high_freight_count)

                if high_freight_categories:
                    st.info(f"**High Freight Categories**: {', '.join(high_freight_categories[:3])}")

            # Product Dimensions Analysis
            st.subheader("📏 Product Dimensions Impact on Freight")

            if all(col in df_products.columns for col in ['product_weight_g', 'volumetric_weight_kg', 'avg_freight_percentage']):
                # Filter products with dimension data
                dims_data = df_products[
                    df_products['product_weight_g'].notna() &
                    df_products['volumetric_weight_kg'].notna()
                ].copy()

                if not dims_data.empty:
                    # Weight vs Freight correlation
                    col1, col2 = st.columns(2)

                    with col1:
                        fig = px.scatter(
                            dims_data.head(200),
                            x='product_weight_g',
                            y='avg_freight_percentage',
                            color='display_category',
                            title="Product Weight vs Freight % (Top 200 Products)",
                            labels={
                                'product_weight_g': 'Weight (grams)',
                                'avg_freight_percentage': 'Freight % of Price',
                                'display_category': 'Category'
                            },
                            hover_data=['product_id', 'total_revenue_usd']
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        fig = px.scatter(
                            dims_data.head(200),
                            x='volumetric_weight_kg',
                            y='avg_freight_percentage',
                            color='display_category',
                            title="Volumetric Weight vs Freight % (Top 200)",
                            labels={
                                'volumetric_weight_kg': 'Volumetric Weight (kg)',
                                'avg_freight_percentage': 'Freight % of Price',
                                'display_category': 'Category'
                            },
                            hover_data=['product_id', 'total_revenue_usd']
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    # Dimensions insights
                    st.markdown("**Dimensions vs Freight Insights:**")

                    # Calculate correlations
                    weight_corr = dims_data['product_weight_g'].corr(dims_data['avg_freight_percentage'])
                    vol_corr = dims_data['volumetric_weight_kg'].corr(dims_data['avg_freight_percentage'])

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        avg_weight = dims_data['product_weight_g'].mean()
                        st.metric("Avg Product Weight", f"{avg_weight:,.0f} g")

                    with col2:
                        avg_vol_weight = dims_data['volumetric_weight_kg'].mean()
                        st.metric("Avg Volumetric Weight", f"{avg_vol_weight:.2f} kg")

                    with col3:
                        heavy_products = len(dims_data[dims_data['product_weight_g'] > 5000])
                        st.metric("Heavy Products (>5kg)", heavy_products)

                    st.info(f"""
                    **Correlation Analysis:**
                    - Weight vs Freight %: {weight_corr:.3f}
                    - Volumetric Weight vs Freight %: {vol_corr:.3f}
                    - {'Strong' if abs(weight_corr) > 0.5 else 'Weak'} correlation between actual weight and freight cost
                    - {'Volumetric' if abs(vol_corr) > abs(weight_corr) else 'Actual'} weight appears more influential
                    """)

                    # Freight optimization opportunities
                    st.subheader("📦 Freight Optimization Opportunities")

                    # Identify products with high volumetric vs actual weight ratio
                    dims_data['vol_to_actual_ratio'] = dims_data['volumetric_weight_kg'] / (dims_data['product_weight_g'] / 1000)
                    inefficient_products = dims_data[dims_data['vol_to_actual_ratio'] > 2].nlargest(10, 'total_revenue_usd')

                    if not inefficient_products.empty:
                        fig = px.bar(
                            inefficient_products,
                            x='vol_to_actual_ratio',
                            y='product_id',
                            orientation='h',
                            title="Top 10 Products with High Volume-to-Weight Ratio (Packaging Optimization Opportunities)",
                            labels={
                                'vol_to_actual_ratio': 'Volumetric / Actual Weight Ratio',
                                'product_id': 'Product ID'
                            },
                            color='vol_to_actual_ratio',
                            color_continuous_scale='Reds',
                            hover_data=['display_category', 'total_revenue_usd']
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        st.warning(f"""
                        **Optimization Alert:**
                        Found {len(inefficient_products)} high-revenue products with excessive packaging (vol/weight ratio > 2).
                        Optimizing packaging for these products could reduce freight costs significantly.
                        """)
                else:
                    st.info("Product dimension data not available for analysis")

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

            # Customer Cohort Retention Analysis
            st.subheader("📅 Customer Cohort Retention Analysis")

            if 'first_order_date' in df_customers.columns and 'last_order_date' in df_customers.columns:
                # Create cohort data from customer segments
                cohort_data = df_customers.copy()
                cohort_data['first_order_month'] = pd.to_datetime(cohort_data['first_order_date']).dt.to_period('M')
                cohort_data['last_order_month'] = pd.to_datetime(cohort_data['last_order_date']).dt.to_period('M')

                # Calculate cohort periods
                cohort_data['cohort_periods'] = (
                    cohort_data['last_order_month'] - cohort_data['first_order_month']
                ).apply(lambda x: x.n if pd.notna(x) else 0)

                # Group by cohort
                cohort_grouped = cohort_data.groupby('first_order_month').agg({
                    'customer_unique_id': 'count',
                    'total_spent_usd': 'sum'
                }).reset_index()
                cohort_grouped.columns = ['cohort_month', 'customer_count', 'cohort_revenue']

                # Calculate retention by cohort and period
                retention_data = []
                for cohort in cohort_data['first_order_month'].unique():
                    if pd.notna(cohort):
                        cohort_customers = cohort_data[cohort_data['first_order_month'] == cohort]
                        total_customers = len(cohort_customers)

                        for period in range(0, 13):  # 0-12 months
                            retained = len(cohort_customers[cohort_customers['cohort_periods'] >= period])
                            retention_rate = (retained / total_customers * 100) if total_customers > 0 else 0

                            retention_data.append({
                                'cohort': str(cohort),
                                'period': period,
                                'retention_rate': retention_rate,
                                'customers_retained': retained
                            })

                if retention_data:
                    retention_df = pd.DataFrame(retention_data)

                    # Pivot for heatmap
                    retention_pivot = retention_df.pivot(
                        index='cohort',
                        columns='period',
                        values='retention_rate'
                    ).fillna(0)

                    # Sort by cohort (most recent first)
                    retention_pivot = retention_pivot.sort_index(ascending=False)

                    # Cohort retention heatmap
                    fig = px.imshow(
                        retention_pivot,
                        title="Cohort Retention Heatmap (%)",
                        labels=dict(x="Months Since First Purchase", y="Cohort Month", color="Retention %"),
                        color_continuous_scale='RdYlGn',
                        zmin=0,
                        zmax=100,
                        text_auto='.0f',
                        aspect='auto'
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)

                    # Cohort retention curves
                    st.subheader("Cohort Retention Curves")

                    # Select top 6 cohorts for clarity
                    top_cohorts = retention_pivot.head(6).index.tolist()
                    retention_curves = retention_df[retention_df['cohort'].isin([str(c) for c in top_cohorts])]

                    fig = px.line(
                        retention_curves,
                        x='period',
                        y='retention_rate',
                        color='cohort',
                        title="Retention Curves by Cohort (Top 6 Recent Cohorts)",
                        labels={
                            'period': 'Months Since First Purchase',
                            'retention_rate': 'Retention Rate (%)',
                            'cohort': 'Cohort Month'
                        },
                        markers=True
                    )
                    fig.update_layout(height=400, hovermode='x unified')
                    fig.update_yaxes(range=[0, 105])
                    st.plotly_chart(fig, use_container_width=True)

                    # Cohort insights
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        avg_1month = retention_pivot[1].mean() if 1 in retention_pivot.columns else 0
                        st.metric("Avg 1-Month Retention", f"{avg_1month:.1f}%")

                    with col2:
                        avg_3month = retention_pivot[3].mean() if 3 in retention_pivot.columns else 0
                        st.metric("Avg 3-Month Retention", f"{avg_3month:.1f}%")

                    with col3:
                        avg_6month = retention_pivot[6].mean() if 6 in retention_pivot.columns else 0
                        st.metric("Avg 6-Month Retention", f"{avg_6month:.1f}%")

                    st.info("""
                    **Cohort Retention Insights:**
                    - Each row represents a cohort (customers who made first purchase in that month)
                    - Each column shows retention after N months
                    - 100% at period 0 = all customers in cohort
                    - Declining values show how many customers returned over time
                    """)

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

        # City-Level Bubble Map
        st.subheader("🎈 City-Level Bubble Map")

        # Get all cities with their metrics
        all_city_sales = df_geo_filtered.groupby(['customer_state', 'customer_city']).agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum'
        }).reset_index().sort_values('total_revenue_usd', ascending=False)

        # Add city_state for display
        all_city_sales['city_state'] = all_city_sales['customer_city'] + ', ' + all_city_sales['customer_state']
        all_city_sales['avg_order_value'] = all_city_sales['total_revenue_usd'] / all_city_sales['order_count']

        # Filter for top cities to avoid overcrowding
        top_n_cities = st.slider("Number of cities to display", min_value=10, max_value=100, value=30, step=10, key="city_bubble_slider")
        bubble_data = all_city_sales.head(top_n_cities)

        # Create bubble chart (using scatter with size)
        fig = px.scatter(
            bubble_data,
            x='order_count',
            y='total_revenue_usd',
            size='avg_order_value',
            color='customer_state',
            hover_name='city_state',
            hover_data={
                'order_count': ':,',
                'total_revenue_usd': ':$,.0f',
                'avg_order_value': ':$,.2f',
                'customer_state': False
            },
            title=f"Top {top_n_cities} Cities: Revenue vs Order Count (Bubble Size = AOV)",
            labels={
                'order_count': 'Order Count',
                'total_revenue_usd': 'Revenue (USD)',
                'customer_state': 'State'
            },
            size_max=60
        )
        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        **Bubble Map Insights:**
        - **X-axis**: Order volume (how many orders)
        - **Y-axis**: Revenue (how much money)
        - **Bubble size**: Average Order Value (AOV)
        - **Color**: State
        - Large bubbles in top-right = High revenue cities with high AOV
        """)

        # Regional Performance Comparison
        st.subheader("🗺️ Regional Performance Analysis")

        # Brazilian regions mapping
        region_mapping = {
            # North
            'AC': 'North', 'AP': 'North', 'AM': 'North', 'PA': 'North',
            'RO': 'North', 'RR': 'North', 'TO': 'North',
            # Northeast
            'AL': 'Northeast', 'BA': 'Northeast', 'CE': 'Northeast',
            'MA': 'Northeast', 'PB': 'Northeast', 'PE': 'Northeast',
            'PI': 'Northeast', 'RN': 'Northeast', 'SE': 'Northeast',
            # Central-West
            'DF': 'Central-West', 'GO': 'Central-West',
            'MT': 'Central-West', 'MS': 'Central-West',
            # Southeast
            'ES': 'Southeast', 'MG': 'Southeast',
            'RJ': 'Southeast', 'SP': 'Southeast',
            # South
            'PR': 'South', 'RS': 'South', 'SC': 'South'
        }

        # Add region to geographic data
        state_sales_regional = state_sales.copy()
        state_sales_regional['region'] = state_sales_regional['customer_state'].map(region_mapping)

        # Regional aggregation
        regional_sales = state_sales_regional.groupby('region').agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum'
        }).reset_index().sort_values('total_revenue_usd', ascending=False)

        regional_sales['avg_order_value'] = regional_sales['total_revenue_usd'] / regional_sales['order_count']

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                regional_sales,
                x='region',
                y='total_revenue_usd',
                title="Revenue by Region",
                labels={'total_revenue_usd': 'Revenue (USD)', 'region': 'Region'},
                color='region',
                text='total_revenue_usd'
            )
            fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                regional_sales,
                x='region',
                y='order_count',
                title="Orders by Region",
                labels={'order_count': 'Order Count', 'region': 'Region'},
                color='region',
                text='order_count'
            )
            fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

        # Regional comparison table
        st.subheader("Regional Comparison Table")
        regional_sales['revenue_share_%'] = (regional_sales['total_revenue_usd'] / regional_sales['total_revenue_usd'].sum() * 100).round(2)
        regional_sales['orders_share_%'] = (regional_sales['order_count'] / regional_sales['order_count'].sum() * 100).round(2)

        display_regional = regional_sales[['region', 'total_revenue_usd', 'revenue_share_%',
                                          'order_count', 'orders_share_%', 'avg_order_value']].copy()

        st.dataframe(display_regional.style.format({
            'total_revenue_usd': '${:,.0f}',
            'revenue_share_%': '{:.2f}%',
            'order_count': '{:,.0f}',
            'orders_share_%': '{:.2f}%',
            'avg_order_value': '${:,.2f}'
        }), use_container_width=True)

        # State-level breakdown by region
        st.subheader("State Performance by Region")

        selected_region = st.selectbox(
            "Select Region",
            options=sorted(region_mapping.values()),
            key="region_selector"
        )

        states_in_region = [state for state, region in region_mapping.items() if region == selected_region]
        region_state_sales = state_sales_regional[
            state_sales_regional['customer_state'].isin(states_in_region)
        ].sort_values('total_revenue_usd', ascending=False)

        fig = px.bar(
            region_state_sales,
            x='total_revenue_usd',
            y='customer_state',
            orientation='h',
            title=f"States in {selected_region} Region by Revenue",
            labels={'total_revenue_usd': 'Revenue (USD)', 'customer_state': 'State'},
            color='total_revenue_usd',
            color_continuous_scale='Blues'
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

        # Enhanced Multi-Indicator Sensitivity Analysis
        if not df_time_series.empty:
            st.subheader("🔍 Multi-Indicator Sensitivity Analysis")
            st.markdown("Analyze how categories respond to different economic indicators")

            # Merge category data with time series to get all indicators
            if 'order_month' in df_cat_filtered.columns and 'order_date' in df_time_series.columns:
                # Convert to same format for joining
                df_cat_with_indicators = df_cat_filtered.copy()
                df_cat_with_indicators['order_date'] = pd.to_datetime(df_cat_with_indicators['order_month'])

                # Get monthly averages of economic indicators
                monthly_indicators = df_time_series.groupby([
                    df_time_series['order_date'].dt.to_period('M')
                ]).agg({
                    'avg_exchange_rate': 'mean',
                    'inflation_rate': 'mean',
                    'interest_rate': 'mean',
                    'daily_revenue_usd': 'sum'
                }).reset_index()
                monthly_indicators['order_month'] = monthly_indicators['order_date'].dt.to_timestamp()

                # Calculate correlations by category
                category_correlations = []

                for category in df_cat_with_indicators['display_category'].unique():
                    if pd.notna(category):
                        cat_data = df_cat_with_indicators[
                            df_cat_with_indicators['display_category'] == category
                        ].groupby('order_month').agg({
                            'total_revenue_usd': 'sum',
                            'order_count': 'sum'
                        }).reset_index()

                        if len(cat_data) > 3:  # Need at least 3 data points
                            # Merge with indicators
                            merged = cat_data.merge(
                                monthly_indicators[['order_month', 'avg_exchange_rate', 'inflation_rate', 'interest_rate']],
                                on='order_month',
                                how='left'
                            ).dropna()

                            if len(merged) > 2:
                                corr_exchange = merged['total_revenue_usd'].corr(merged['avg_exchange_rate'])
                                corr_inflation = merged['total_revenue_usd'].corr(merged['inflation_rate'])
                                corr_interest = merged['total_revenue_usd'].corr(merged['interest_rate'])

                                category_correlations.append({
                                    'category': category,
                                    'exchange_rate_corr': corr_exchange,
                                    'inflation_corr': corr_inflation,
                                    'interest_rate_corr': corr_interest
                                })

                if category_correlations:
                    corr_df = pd.DataFrame(category_correlations)

                    # Selector for indicator
                    indicator = st.selectbox(
                        "Select Economic Indicator",
                        options=['Exchange Rate (USD/BRL)', 'Inflation (IPCA)', 'Interest Rate (SELIC)'],
                        key="indicator_selector"
                    )

                    indicator_col_map = {
                        'Exchange Rate (USD/BRL)': 'exchange_rate_corr',
                        'Inflation (IPCA)': 'inflation_corr',
                        'Interest Rate (SELIC)': 'interest_rate_corr'
                    }

                    selected_col = indicator_col_map[indicator]

                    # Sort and display
                    corr_display = corr_df.sort_values(selected_col, ascending=False).head(15)

                    fig = px.bar(
                        corr_display,
                        x=selected_col,
                        y='category',
                        orientation='h',
                        title=f"Category Correlation with {indicator}",
                        labels={selected_col: 'Correlation Coefficient', 'category': 'Category'},
                        color=selected_col,
                        color_continuous_scale='RdBu',
                        range_color=[-1, 1]
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.info(f"""
                    **Correlation Interpretation ({indicator}):**
                    - **Positive (> 0.5)**: Strong positive relationship - sales increase when {indicator.split('(')[0].strip()} increases
                    - **Negative (< -0.5)**: Strong negative relationship - sales decrease when {indicator.split('(')[0].strip()} increases
                    - **Near Zero (-0.3 to 0.3)**: Weak or no relationship with {indicator.split('(')[0].strip()}
                    """)

                    # Heatmap of all correlations
                    st.subheader("Category Sensitivity Heatmap")

                    # Prepare data for heatmap
                    heatmap_data = corr_df.set_index('category')[
                        ['exchange_rate_corr', 'inflation_corr', 'interest_rate_corr']
                    ].head(15)

                    heatmap_data.columns = ['Exchange Rate', 'Inflation (IPCA)', 'Interest Rate (SELIC)']

                    fig = px.imshow(
                        heatmap_data.T,
                        title="Economic Indicator Sensitivity by Category",
                        labels=dict(x="Category", y="Economic Indicator", color="Correlation"),
                        color_continuous_scale='RdBu',
                        zmin=-1,
                        zmax=1,
                        text_auto='.2f',
                        aspect='auto'
                    )
                    fig.update_xaxes(tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)

        # Raw data view
        st.subheader("📋 Detailed Data")
        if st.checkbox("Show raw data"):
            st.dataframe(df_cat_filtered.head(100))

if __name__ == "__main__":
    main()

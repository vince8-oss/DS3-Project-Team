"""
Brazilian Sales Economic Impact Dashboard
Interactive visualization of how economic indicators affect sales
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from datetime import datetime, timedelta
import numpy as np

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
    credentials_path = "/home/eugen/ProjectM2/meltano-bigquery-py311/apc-data-science-and-ai-1c8f5b9e267b.json"
    return bigquery.Client.from_service_account_json(credentials_path)

# Load data with caching
@st.cache_data(ttl=3600)
def load_category_data():
    """Load category performance data"""
    client = get_bigquery_client()
    query = """
    SELECT *
    FROM `apc-data-science-and-ai.brazilian_sales_marts.fct_category_performance_economics`
    WHERE product_category_name IS NOT NULL
    ORDER BY order_month DESC
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=3600)
def load_geographic_data():
    """Load geographic sales data"""
    client = get_bigquery_client()
    query = """
    SELECT *
    FROM `apc-data-science-and-ai.brazilian_sales_marts.fct_geographic_sales_economics`
    WHERE product_category_name IS NOT NULL
    ORDER BY order_month DESC
    """
    return client.query(query).to_dataframe()

@st.cache_data(ttl=3600)
def load_customer_data():
    """Load customer purchase data"""
    client = get_bigquery_client()
    query = """
    SELECT *
    FROM `apc-data-science-and-ai.brazilian_sales_marts.fct_customer_purchases_economics`
    LIMIT 100000
    """
    return client.query(query).to_dataframe()

# Main app
def main():
    st.title("🇧🇷 Brazilian E-commerce Economic Impact Dashboard")
    st.markdown("### Analyze how exchange rates, inflation, and interest rates affect sales")
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Load data
    with st.spinner("Loading data..."):
        df_category = load_category_data()
        df_geo = load_geographic_data()
    
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
    
    # Product category filter
    categories = sorted(df_category['product_category_name'].unique())
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
        (df_category['product_category_name'].isin(selected_categories)) &
        (df_category['exchange_rate_period'].isin(selected_exchange))
    ]
    
    df_geo_filtered = df_geo[
        (df_geo['customer_state'].isin(selected_states)) &
        (df_geo['product_category_name'].isin(selected_categories))
    ]
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Overview", 
        "🏷️ Category Analysis", 
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
    
    # TAB 2: Category Analysis
    with tab2:
        st.header("🏷️ Product Category Performance")
        
        # Category performance by exchange rate period
        st.subheader("Category Performance by Economic Period")
        
        category_comparison = df_cat_filtered.groupby(
            ['product_category_name', 'exchange_rate_period']
        ).agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum'
        }).reset_index()
        
        fig = px.bar(
            category_comparison,
            x='product_category_name',
            y='total_revenue_usd',
            color='exchange_rate_period',
            title="Revenue by Category and Exchange Rate Period",
            labels={'total_revenue_usd': 'Revenue (USD)', 'product_category_name': 'Category'},
            barmode='group',
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top categories
        st.subheader("📊 Top Performing Categories")
        top_categories = df_cat_filtered.groupby('product_category_name').agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum',
            'avg_exchange_rate': 'mean'
        }).reset_index().sort_values('total_revenue_usd', ascending=False).head(10)
        
        fig = px.bar(
            top_categories,
            x='total_revenue_usd',
            y='product_category_name',
            orientation='h',
            title="Top 10 Categories by Revenue",
            labels={'total_revenue_usd': 'Revenue (USD)', 'product_category_name': 'Category'},
            color='total_revenue_usd',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Category trend
        st.subheader("📈 Category Trend Over Time")
        selected_cat_trend = st.selectbox(
            "Select category to view trend",
            options=sorted(selected_categories)
        )
        
        cat_trend = df_cat_filtered[
            df_cat_filtered['product_category_name'] == selected_cat_trend
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
    
    # TAB 3: Geographic Analysis
    with tab3:
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
        
        # Geographic heatmap
        st.subheader("🗺️ State Performance Heatmap")
        
        state_category = df_geo_filtered.groupby(
            ['customer_state', 'product_category_name']
        ).agg({
            'order_count': 'sum'
        }).reset_index()
        
        # Pivot for heatmap
        heatmap_data = state_category.pivot(
            index='customer_state',
            columns='product_category_name',
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
    
    # TAB 4: Economic Impact
    with tab4:
        st.header("💱 Economic Indicators Impact")
        
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
            ['product_category_name', 'exchange_rate_period']
        ).agg({
            'order_count': 'sum',
            'total_revenue_usd': 'sum'
        }).reset_index()
        
        # Calculate variance
        category_variance = category_elasticity.pivot(
            index='product_category_name',
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
                y='product_category_name',
                orientation='h',
                title="Category Sensitivity to Exchange Rate (% Change)",
                labels={'elasticity': 'Change (%)', 'product_category_name': 'Category'},
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
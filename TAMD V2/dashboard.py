"""
dashboard.py - Interactive Streamlit Dashboard for TAMD Fashion Inventory System
Run with: streamlit run dashboard.py
Now supports REAL DATA upload and processing
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import warnings
import os

warnings.filterwarnings('ignore')

# Import modules
from data_loader import load_and_preprocess_real_data, PRODUCT_GROUPS
from tamd_core import TAMDAnalyzer
from inventory_manager import InventoryManager

# ============================================
# PAGE CONFIGURATION
# ============================================

st.set_page_config(
    page_title="TAMD Fashion Inventory",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-top: 0;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .warning-text {
        color: #ff4b4b;
        font-weight: bold;
    }
    .success-text {
        color: #00cc66;
        font-weight: bold;
    }
    .real-data-badge {
        background-color: #4CAF50;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .sim-data-badge {
        background-color: #FFA726;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================

st.markdown('<p class="main-header">👗 TAMD Fashion Inventory Management System</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">A Simplified TAMD Framework for Seasonal Inventory Management in Fashion SMEs</p>', unsafe_allow_html=True)

# ============================================
# GENERATE SIMULATED DATA (For Reference Only)
# ============================================

def generate_simulated_data(n_weeks=104, n_products_per_group=3):
    """Generate simulated data using the original generator (for comparison only)"""
    from data_generator import FashionDataGenerator
    generator = FashionDataGenerator(
        n_weeks=n_weeks,
        n_products_per_group=n_products_per_group,
        random_seed=42
    )
    sales_df, products_df = generator.generate()
    group_sales = generator.aggregate_by_group()
    return sales_df, products_df, group_sales, generator

# ============================================
# SIDEBAR CONTROLS
# ============================================

with st.sidebar:
    st.header("⚙️ System Controls")
    
    # Data Source Selection
    st.subheader("📁 Data Source")
    data_source = st.radio(
        "Choose Data Source:",
        ["Real Data (Upload CSV)", "Simulated Data (Reference)"],
        index=0
    )
    
    if data_source == "Real Data (Upload CSV)":
        uploaded_file = st.file_uploader(
            "Upload your fashion sales CSV", 
            type=['csv'],
            help="Upload a CSV with columns: date, store, sku, sales"
        )
        
        if uploaded_file is not None:
            if st.button("🚀 Load & Process Real Data", type="primary", use_container_width=True):
                with st.spinner("Loading and preprocessing real data..."):
                    try:
                        # Save uploaded file temporarily
                        with open("temp_upload.csv", "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Load and preprocess
                        sales_df, products_df, group_sales, summary = load_and_preprocess_real_data("temp_upload.csv")
                        
                        # Store in session state
                        st.session_state.sales_df = sales_df
                        st.session_state.products_df = products_df
                        st.session_state.group_sales = group_sales
                        st.session_state.data_source = "real"
                        st.session_state.tamd_results = {}
                        st.session_state.data_generated = True
                        st.session_state.summary = summary
                        
                        # Clean up
                        os.remove("temp_upload.csv")
                        
                        st.success(f"✅ Loaded real data: {len(sales_df):,} weekly records, {len(products_df)} products!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error loading data: {str(e)}")
        
        # Show sample data if already loaded
        if st.session_state.get('data_source') == 'real':
            st.markdown("---")
            st.caption("✅ Real data currently loaded")
            if 'summary' in st.session_state:
                st.caption(f"📊 {st.session_state.summary['total_weekly_records']} records, {st.session_state.summary['total_products']} products")
    
    else:
        # Simulated Data (for reference only)
        st.subheader("📊 Simulated Data (Reference)")
        st.caption("⚠️ This is for comparison only. Use real data for validation.")
        
        n_weeks = st.slider("Weeks", 52, 156, 104)
        n_products = st.slider("Products per Group", 2, 4, 3)
        
        if st.button("🔄 Generate Simulated", type="primary", use_container_width=True):
            with st.spinner("Generating simulated data..."):
                sales_df, products_df, group_sales, generator = generate_simulated_data(n_weeks, n_products)
                
                st.session_state.sales_df = sales_df
                st.session_state.products_df = products_df
                st.session_state.group_sales = group_sales
                st.session_state.data_source = "simulated"
                st.session_state.tamd_results = {}
                st.session_state.data_generated = True
                
            st.success(f"✅ Generated {len(sales_df):,} records!")
            st.rerun()
    
    st.divider()
    
    # TAMD Analysis Section
    if st.session_state.get('data_generated', False):
        st.subheader("📈 TAMD Analysis")
        
        groups = st.session_state.group_sales['product_group'].unique().tolist()
        selected_group = st.selectbox("Select Product Group", groups)
        
        if st.button("🔬 Run TAMD Analysis", type="primary", use_container_width=True):
            with st.spinner(f"Running TAMD analysis on {selected_group}..."):
                group_data = st.session_state.group_sales[
                    st.session_state.group_sales['product_group'] == selected_group
                ]
                sales_series = group_data['quantity_sold'].values
                
                analyzer = TAMDAnalyzer()
                analyzer.load_data(sales_series)
                results = analyzer.run_pipeline(verbose=False)
                
                st.session_state.tamd_results[selected_group] = {
                    'analyzer': analyzer,
                    'results': results,
                    'forecast': results['forecast']
                }
                
            st.success(f"✅ TAMD Analysis Complete for {selected_group}!")
            st.rerun()
    
    st.divider()
    
    # Info Section
    st.subheader("ℹ️ About")
    
    if st.session_state.get('data_generated', False):
        source = st.session_state.get('data_source', 'unknown')
        if source == 'real':
            st.markdown('<span class="real-data-badge">✅ Real Data</span>', unsafe_allow_html=True)
        elif source == 'simulated':
            st.markdown('<span class="sim-data-badge">🔄 Simulated Data</span>', unsafe_allow_html=True)
    
    st.info("""
    **TAMD Framework Components:**
    - **T** - Trend (Long-term direction)
    - **A** - Amplitude (Seasonal variation)
    - **M** - Momentum (Recent changes)
    - **D** - Demand (Forecast)
    
    **Inventory Metrics:**
    - **SS** - Safety Stock (Emergency reserve)
    - **ROP** - Reorder Point (When to order)
    """)

# ============================================
# MAIN CONTENT TABS
# ============================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
    "📈 TAMD Analysis", 
    "📦 Inventory", 
    "📋 Data Viewer",
    "ℹ️ Documentation"
])

# ============================================
# TAB 1: DASHBOARD
# ============================================

with tab1:
    if not st.session_state.get('data_generated', False):
        st.info("👈 **Welcome!** Upload real data in the sidebar to start.")
    else:
        st.header("📊 Sales Dashboard")
        
        sales_df = st.session_state.sales_df
        products_df = st.session_state.products_df
        group_sales = st.session_state.group_sales
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Product Groups", len(group_sales['product_group'].unique()))
        with col2:
            st.metric("Total Products", len(products_df))
        with col3:
            total_units = sales_df['quantity_sold'].sum()
            st.metric("Total Units Sold", f"{total_units:,.0f}")
        with col4:
            st.metric("Data Source", st.session_state.get('data_source', 'unknown').title())
        
        st.divider()
        
        st.subheader("📈 Sales by Product Group")
        
        fig = px.line(
            group_sales,
            x='week',
            y='quantity_sold',
            color='product_group',
            title='Weekly Sales by Product Group (Real Data)',
            labels={'week': 'Week', 'quantity_sold': 'Units Sold', 'product_group': 'Product Group'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📊 Group Performance Summary")
        
        group_summary = group_sales.groupby('product_group').agg({
            'quantity_sold': ['mean', 'sum', 'max']
        }).round(0)
        group_summary.columns = ['Avg Weekly', 'Total Units', 'Peak Week']
        group_summary = group_summary.sort_values('Total Units', ascending=False)
        
        st.dataframe(group_summary, use_container_width=True)

# ============================================
# TAB 2: TAMD ANALYSIS
# ============================================

with tab2:
    if not st.session_state.get('data_generated', False):
        st.info("Load data first to see TAMD analysis")
    elif not st.session_state.tamd_results:
        st.info("Select a group and click 'Run TAMD Analysis' in the sidebar")
    else:
        st.header("📈 TAMD Analysis Results (Real Data)")
        
        selected_group = st.session_state.get('selected_group_for_display', 
                                              list(st.session_state.tamd_results.keys())[0])
        
        if selected_group in st.session_state.tamd_results:
            results = st.session_state.tamd_results[selected_group]['results']
            analyzer = st.session_state.tamd_results[selected_group]['analyzer']
            
            st.subheader(f"🎯 Forecast for {selected_group}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("TAMD Forecast", f"{results['forecast']:.0f} units", 
                         delta=f"vs {results['forecast'] - analyzer.data[-1]:.0f} from last week")
            with col2:
                st.metric("Trend Complexity", f"{results['complexities']['trend']:.3f}")
            with col3:
                st.metric("Seasonal Complexity", f"{results['complexities']['seasonal']:.3f}")
            
            st.subheader("📊 Decomposed Modes")
            
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(results['trend'], label='Trend (Long-term)', linewidth=2)
            ax.plot(results['seasonal'], label='Seasonal (Pattern)', linewidth=2)
            ax.plot(results['residual'], label='Residual (Noise)', alpha=0.7)
            ax.legend()
            ax.set_xlabel('Week')
            ax.set_ylabel('Units')
            ax.set_title(f'{selected_group} - TAMD Decomposition (Real Data)')
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            
            st.subheader("📊 Complexity Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig2, ax2 = plt.subplots(figsize=(6, 4))
                complexities = results['complexities']
                methods = results['methods']
                bars = ax2.bar(complexities.keys(), complexities.values(), 
                              color=['red', 'green', 'orange'])
                ax2.set_title('Mode Complexity')
                ax2.set_ylabel('Complexity Score')
                ax2.set_ylim(0, 1)
                for bar, mode in zip(bars, methods.keys()):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                            methods[mode], ha='center', va='bottom', fontsize=8)
                st.pyplot(fig2)
            
            with col2:
                actual = analyzer.data[-1]
                errors = analyzer.evaluate_accuracy(actual)
                
                fig3, ax3 = plt.subplots(figsize=(6, 4))
                methods_list = list(errors.keys())
                errors_list = list(errors.values())
                bars = ax3.barh(methods_list, errors_list, color=['gray', 'gray', 'green'])
                ax3.set_xlabel('Error (%)')
                ax3.set_title('Forecast Accuracy Comparison (Real Data)')
                ax3.bar_label(bars, fmt='%.1f%%')
                st.pyplot(fig3)
            
            with st.expander("📖 How to Interpret These Results"):
                st.markdown("""
                **TAMD Decomposition:**
                - **Trend**: The underlying growth or decline (smooth line)
                - **Seasonal**: Repeating yearly patterns (oscillating line)
                - **Residual**: Random fluctuations (noisy line)
                
                **Complexity Scores:**
                - **< 0.3**: Very predictable
                - **0.3 - 0.6**: Moderately predictable
                - **> 0.6**: Hard to predict
                
                **Forecast Accuracy:**
                - Lower error percentage = better forecast
                - TAMD should outperform simple methods
                """)

# ============================================
# TAB 3: INVENTORY
# ============================================

with tab3:
    if not st.session_state.get('data_generated', False):
        st.info("Load data first to see inventory recommendations")
    else:
        st.header("📦 Inventory Recommendations")
        
        manager = InventoryManager()
        manager.load_data(st.session_state.sales_df, st.session_state.products_df)
        
        group_forecasts = {group: data['forecast'] for group, data in st.session_state.tamd_results.items()}
        
        inventory_df = manager.calculate_all_products(group_forecasts if group_forecasts else None)
        
        col1, col2 = st.columns(2)
        with col1:
            all_groups = ["All"] + list(inventory_df['product_group'].unique())
            filter_group = st.selectbox("Filter by Group", all_groups)
        with col2:
            filter_status = st.selectbox("Filter by Status", ["All", "⚠️ ORDER NOW", "✅ OK"])
        
        filtered_df = inventory_df.copy()
        if filter_group != "All":
            filtered_df = filtered_df[filtered_df['product_group'] == filter_group]
        if filter_status != "All":
            filtered_df = filtered_df[filtered_df['stock_status'] == filter_status]
        
        display_cols = ['product_name', 'product_group', 'avg_weekly_sales', 
                       'safety_stock', 'reorder_point', 'current_stock', 'stock_status', 'recommended_order']
        
        st.dataframe(filtered_df[display_cols], use_container_width=True)
        
        st.subheader("📊 Inventory Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            needs_order = len(inventory_df[inventory_df['needs_reorder']])
            st.metric("Products Needing Reorder", needs_order)
        with col2:
            avg_ss = inventory_df['safety_stock'].mean()
            st.metric("Avg Safety Stock", f"{avg_ss:.0f} units")
        with col3:
            avg_rop = inventory_df['reorder_point'].mean()
            st.metric("Avg Reorder Point", f"{avg_rop:.0f} units")
        
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Inventory Report (CSV)",
            data=csv,
            file_name=f"inventory_report.csv",
            mime="text/csv"
        )

# ============================================
# TAB 4: DATA VIEWER
# ============================================

with tab4:
    if not st.session_state.get('data_generated', False):
        st.info("Load data first to view data")
    else:
        st.header("📋 Data Viewer")
        
        data_option = st.selectbox("Select Data", ["Sales Transactions", "Products", "Group Sales"])
        
        if data_option == "Sales Transactions":
            st.dataframe(st.session_state.sales_df.head(100), use_container_width=True)
            st.caption(f"Showing first 100 of {len(st.session_state.sales_df):,} records")
            
        elif data_option == "Products":
            st.dataframe(st.session_state.products_df, use_container_width=True)
            
        else:  # Group Sales
            st.dataframe(st.session_state.group_sales, use_container_width=True)

# ============================================
# TAB 5: DOCUMENTATION
# ============================================

with tab5:
    st.header("ℹ️ System Documentation")
    
    st.markdown("""
    ### 🎯 System Overview
    
    This system implements a **Simplified TAMD (Time Series Adaptive Mode Decomposition)** 
    framework for fashion SME inventory management using **real sales data**.
    
    ### 📁 Data Format
    
    The system expects a CSV file with the following columns:
    - `date`: Transaction date (YYYY-MM-DD)
    - `store`: Store identifier
    - `sku`: Product identifier
    - `sales`: Units sold
    
    ### 🔄 Data Pipeline
    
    1. **Load** real CSV data
    2. **Aggregate** daily sales to weekly
    3. **Assign** each SKU to a seasonal product group
    4. **Run** TAMD analysis on each group
    5. **Generate** inventory recommendations
    
    ### 🧮 Key Formulas
    
    | Metric | Formula | Description |
    |--------|---------|-------------|
    | **Safety Stock (SS)** | `2 × Std Dev of Weekly Sales` | Emergency reserve |
    | **Reorder Point (ROP)** | `(Avg Weekly × Lead Time) + SS` | Stock level that triggers new order |
    | **Recommended Order** | `4 × Avg Weekly Sales` | Suggested order quantity |
    
    ### 📊 TAMD Framework
    
    | Component | What It Does |
    |-----------|--------------|
    | **Trend (T)** | Extracts long-term direction |
    | **Amplitude (A)** | Measures seasonal variation |
    | **Momentum (M)** | Detects recent changes |
    | **Demand (D)** | Combines all components for forecast |
    
    ### 📚 Reference
    
    Based on: Zhou et al. (2026) *"Time series adaptive mode decomposition (TAMD): 
    Method for improving fo

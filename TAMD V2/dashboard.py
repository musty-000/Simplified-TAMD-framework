"""
dashboard.py - Interactive Streamlit Dashboard for TAMD Fashion Inventory System
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import modules
from data_generator import FashionDataGenerator, PRODUCT_GROUPS
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
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================

st.markdown('<p class="main-header">👗 TAMD Fashion Inventory Management System</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">A Simplified TAMD Framework for Seasonal Inventory Management in Fashion SMEs</p>', unsafe_allow_html=True)

# ============================================
# SIDEBAR CONTROLS
# ============================================

with st.sidebar:
    st.header("⚙️ System Controls")
    
    # Data Generation Section
    st.subheader("📊 Data Generation")
    n_weeks = st.slider("Number of Weeks", 52, 156, 104, 
                        help="More weeks = more historical data for analysis")
    n_products = st.slider("Products per Group", 2, 4, 3,
                          help="How many products in each fashion category")
    
    if st.button("🔄 Generate New Data", type="primary", use_container_width=True):
        with st.spinner("Generating fashion sales data..."):
            generator = FashionDataGenerator(
                n_weeks=n_weeks,
                n_products_per_group=n_products,
                random_seed=42
            )
            sales_df, products_df = generator.generate()
            group_sales = generator.aggregate_by_group()
            
            # Store in session state
            st.session_state.generator = generator
            st.session_state.sales_df = sales_df
            st.session_state.products_df = products_df
            st.session_state.group_sales = group_sales
            st.session_state.tamd_results = {}
            st.session_state.data_generated = True
            
        st.success(f"✅ Generated {len(sales_df):,} sales records!")
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
        st.info("👈 **Welcome!** Click 'Generate New Data' in the sidebar to start.")
    else:
        st.header("📊 Sales Dashboard")
        
        # Metrics Row
        sales_df = st.session_state.sales_df
        products_df = st.session_state.products_df
        group_sales = st.session_state.group_sales
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Product Groups", len(PRODUCT_GROUPS))
        with col2:
            st.metric("Total Products", len(products_df))
        with col3:
            total_revenue = sales_df['revenue'].sum()
            st.metric("Total Revenue", f"${total_revenue:,.0f}")
        with col4:
            total_units = sales_df['quantity_sold'].sum()
            st.metric("Total Units Sold", f"{total_units:,}")
        
        st.divider()
        
        # Group Sales Chart
        st.subheader("📈 Sales by Product Group")
        
        fig = px.line(
            group_sales,
            x='week',
            y='quantity_sold',
            color='product_group',
            title='Weekly Sales by Product Group',
            labels={'week': 'Week', 'quantity_sold': 'Units Sold', 'product_group': 'Product Group'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Group Performance Summary
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
        st.info("Generate data first to see TAMD analysis")
    elif not st.session_state.tamd_results:
        st.info(f"Select a group and click 'Run TAMD Analysis' in the sidebar")
    else:
        st.header("📈 TAMD Analysis Results")
        
        # Show results for selected group
        selected_group = st.session_state.get('selected_group_for_display', 
                                              list(st.session_state.tamd_results.keys())[0])
        
        if selected_group in st.session_state.tamd_results:
            results = st.session_state.tamd_results[selected_group]['results']
            analyzer = st.session_state.tamd_results[selected_group]['analyzer']
            
            # Forecast Display
            st.subheader(f"🎯 Forecast for {selected_group}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("TAMD Forecast", f"{results['forecast']:.0f} units", 
                         delta=f"vs {results['forecast'] - analyzer.data[-1]:.0f} from last week")
            with col2:
                st.metric("Trend Complexity", f"{results['complexities']['trend']:.3f}")
            with col3:
                st.metric("Seasonal Complexity", f"{results['complexities']['seasonal']:.3f}")
            
            # Decomposed Modes Plot
            st.subheader("📊 Decomposed Modes")
            
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(results['trend'], label='Trend (Long-term)', linewidth=2)
            ax.plot(results['seasonal'], label='Seasonal (Pattern)', linewidth=2)
            ax.plot(results['residual'], label='Residual (Noise)', alpha=0.7)
            ax.legend()
            ax.set_xlabel('Week')
            ax.set_ylabel('Units')
            ax.set_title(f'{selected_group} - TAMD Decomposition')
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            
            # Complexity Analysis
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
                # Accuracy Comparison
                actual = analyzer.data[-1]
                errors = analyzer.evaluate_accuracy(actual)
                
                fig3, ax3 = plt.subplots(figsize=(6, 4))
                methods_list = list(errors.keys())
                errors_list = list(errors.values())
                bars = ax3.barh(methods_list, errors_list, color=['gray', 'gray', 'green'])
                ax3.set_xlabel('Error (%)')
                ax3.set_title('Forecast Accuracy Comparison')
                ax3.bar_label(bars, fmt='%.1f%%')
                st.pyplot(fig3)
            
            # Interpretation Guide
            with st.expander("📖 How to Interpret These Results"):
                st.markdown("""
                **TAMD Decomposition:**
                - **Trend**: The underlying growth or decline (smooth line)
                - **Seasonal**: Repeating yearly patterns (oscillating line)
                - **Residual**: Random fluctuations (noisy line)
                
                **Complexity Scores:**
                - **< 0.3**: Very predictable
                - **0.3 - 0.6**: Moderately predictable
                - **> 0.6**: Hard to predict (needs more complex methods)
                
                **Forecast Accuracy:**
                - Lower error percentage = better forecast
                - TAMD should outperform simple methods
                """)

# ============================================
# TAB 3: INVENTORY
# ============================================

with tab3:
    if not st.session_state.get('data_generated', False):
        st.info("Generate data first to see inventory recommendations")
    else:
        st.header("📦 Inventory Recommendations")
        
        # Create inventory manager
        manager = InventoryManager()
        manager.load_data(st.session_state.sales_df, st.session_state.products_df)
        
        # Get group forecasts
        group_forecasts = {group: data['forecast'] for group, data in st.session_state.tamd_results.items()}
        
        # Calculate inventory
        inventory_df = manager.calculate_all_products(group_forecasts if group_forecasts else None)
        
        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            filter_group = st.selectbox("Filter by Group", ["All"] + list(PRODUCT_GROUPS.keys()))
        with col2:
            filter_status = st.selectbox("Filter by Status", ["All", "⚠️ ORDER NOW", "✅ OK"])
        
        # Apply filters
        filtered_df = inventory_df.copy()
        if filter_group != "All":
            filtered_df = filtered_df[filtered_df['product_group'] == filter_group]
        if filter_status != "All":
            filtered_df = filtered_df[filtered_df['stock_status'] == filter_status]
        
        # Display inventory table
        display_cols = ['product_name', 'product_group', 'avg_weekly_sales', 
                       'safety_stock', 'reorder_point', 'current_stock', 'stock_status', 'recommended_order']
        
        st.dataframe(filtered_df[display_cols], use_container_width=True)
        
        # Summary metrics
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
        
        # Download button
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
        st.info("Generate data first to view data")
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
    framework for fashion SME inventory management.
    
    ---
    
    ### 🧮 Key Formulas
    
    | Metric | Formula | Description |
    |--------|---------|-------------|
    | **Safety Stock (SS)** | `2 × Std Dev of Weekly Sales` | Emergency reserve for unexpected demand |
    | **Reorder Point (ROP)** | `(Avg Weekly × Lead Time) + SS` | Stock level that triggers new order |
    | **Recommended Order** | `4 × Avg Weekly Sales` | Suggested order quantity |
    
    ---
    
    ### 📊 TAMD Framework
    
    | Component | What It Does | How It Helps |
    |-----------|--------------|--------------|
    | **Trend (T)** | Extracts long-term direction | Understand business growth |
    | **Amplitude (A)** | Measures seasonal variation | Plan for peak seasons |
    | **Momentum (M)** | Detects recent changes | React to market shifts |
    | **Demand (D)** | Combines all components | Generate accurate forecast |
    
    ---
    
    ### 📁 Output Files
    
    | File | Contents |
    |------|----------|
    | `sales_data.csv` | All sales transactions |
    | `products.csv` | Product catalog |
    | `group_sales.csv` | Group-aggregated sales |
    | `inventory_recommendations.csv` | Per-product inventory recommendations |
    
    ---
    
    ### 📚 Reference
    
    Based on: Zhou et al. (2026) *"Time series adaptive mode decomposition (TAMD): 
    Method for improving forecasting accuracy in the apparel industry."* 
    *Pattern Recognition*, Volume 172.
    
    ---
    
    ### ✨ Your System's Unique Contributions
    
    1. **Simplification**: Making TAMD accessible for SMEs
    2. **Domain Application**: Tailored for fashion retail with 5 product groups
    3. **Actionable Output**: Inventory decisions, not just forecasts
    4. **Multi-Product Framework**: Handles product groups intelligently
    5. **User-Friendly Interface**: Easy for business owners to use
    """)

# ============================================
# FOOTER
# ============================================

st.divider()
st.caption("👗 TAMD Fashion Inventory System | Built with Streamlit | Based on Zhou et al. (2026)")

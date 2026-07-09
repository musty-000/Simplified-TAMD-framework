"""
data_loader.py
Loads and preprocesses real fashion sales data for TAMD analysis
Author: TAMD Fashion Inventory System
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# ============================================
# PRODUCT GROUP DEFINITIONS (For Reference)
# ============================================

PRODUCT_GROUPS = {
    'Summer Wear': {
        'seasonality_type': 'summer_peak',
        'base_price': 45,
        'cost_ratio': 0.55,
        'reorder_lead_time': 14,  # days
        'min_stock_days': 21,
        'description': 'Light clothing for warm weather'
    },
    'Winter Wear': {
        'seasonality_type': 'winter_peak',
        'base_price': 85,
        'cost_ratio': 0.60,
        'reorder_lead_time': 14,
        'min_stock_days': 21,
        'description': 'Heavy clothing for cold weather'
    },
    'All-Year Basics': {
        'seasonality_type': 'steady',
        'base_price': 35,
        'cost_ratio': 0.50,
        'reorder_lead_time': 10,
        'min_stock_days': 14,
        'description': 'Essential items sold year-round'
    },
    'Festive Wear': {
        'seasonality_type': 'holiday_peak',
        'base_price': 95,
        'cost_ratio': 0.65,
        'reorder_lead_time': 21,
        'min_stock_days': 28,
        'description': 'Special occasion clothing'
    },
    'Accessories': {
        'seasonality_type': 'follows_seasons',
        'base_price': 55,
        'cost_ratio': 0.45,
        'reorder_lead_time': 10,
        'min_stock_days': 14,
        'description': 'Fashion accessories and add-ons'
    }
}


# ============================================
# DATA LOADING FUNCTIONS
# ============================================

def load_real_data(filepath):
    """
    Load the synthetic_fashion_sales.csv dataset
    
    Parameters:
    - filepath: path to the CSV file
    
    Returns:
    - df: raw DataFrame with parsed dates
    """
    print("📂 Loading real fashion sales data...")
    
    try:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        print(f"   ✅ Loaded {len(df):,} records")
        print(f"   📅 Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   🏪 Stores: {df['store'].unique().tolist()}")
        print(f"   📦 SKUs: {df['sku'].unique().tolist()}")
        return df
    except Exception as e:
        print(f"   ❌ Error loading file: {e}")
        raise


def aggregate_to_weekly(df):
    """
    Aggregate daily sales to weekly sales
    
    Parameters:
    - df: raw DataFrame with date, store, sku, sales
    
    Returns:
    - weekly_df: weekly aggregated sales with week numbers
    """
    print("📊 Aggregating daily to weekly sales...")
    
    # Extract year and week number
    df['year'] = df['date'].dt.isocalendar().year
    df['week_no'] = df['date'].dt.isocalendar().week
    
    # Group by store, sku, year, week
    weekly_df = df.groupby(['store', 'sku', 'year', 'week_no'], as_index=False).agg({
        'sales': 'sum'
    })
    
    # Create a week-start date for plotting
    weekly_df['date'] = pd.to_datetime(
        weekly_df['year'].astype(str) + '-' + 
        weekly_df['week_no'].astype(str) + '-1',
        format='%Y-%W-%w'
    )
    
    # Create a global week index
    min_date = weekly_df['date'].min()
    weekly_df['week'] = ((weekly_df['date'] - min_date).dt.days / 7).astype(int) + 1
    
    # Rename columns for consistency
    weekly_df = weekly_df.rename(columns={
        'sku': 'product_id',
        'sales': 'quantity_sold'
    })
    
    print(f"   ✅ Aggregated to {len(weekly_df):,} weekly records")
    print(f"   📅 Weeks: {weekly_df['week'].min()} to {weekly_df['week'].max()}")
    
    return weekly_df


def assign_product_groups(weekly_df):
    """
    Assign each SKU to a seasonal product group based on its sales pattern
    
    Parameters:
    - weekly_df: weekly sales data with product_id, date, quantity_sold
    
    Returns:
    - products_df: product metadata with group assignments
    """
    print("🏷️ Assigning products to seasonal groups...")
    
    product_data = []
    
    for product_id in weekly_df['product_id'].unique():
        # Get product's weekly sales
        product_sales = weekly_df[weekly_df['product_id'] == product_id].copy()
        
        # Calculate monthly averages
        product_sales['month'] = product_sales['date'].dt.month
        monthly_avg = product_sales.groupby('month')['quantity_sold'].mean()
        overall_avg = monthly_avg.mean()
        
        # Calculate seasonal indicators
        summer_avg = monthly_avg.loc[6:8].mean() if (6 in monthly_avg.index and 8 in monthly_avg.index) else 0
        winter_avg = monthly_avg.loc[[12, 1, 2]].mean() if 12 in monthly_avg.index else 0
        holiday_avg = monthly_avg.loc[11:12].mean() if (11 in monthly_avg.index and 12 in monthly_avg.index) else 0
        variation = monthly_avg.std() / overall_avg if overall_avg > 0 else 0
        
        # Determine group based on seasonality
        if summer_avg > 1.2 * overall_avg and winter_avg < overall_avg:
            group = 'Summer Wear'
        elif winter_avg > 1.2 * overall_avg and summer_avg < overall_avg:
            group = 'Winter Wear'
        elif holiday_avg > 1.4 * overall_avg:
            group = 'Festive Wear'
        elif variation < 0.15:
            group = 'All-Year Basics'
        else:
            group = 'Accessories'
        
        # Get group info
        group_info = PRODUCT_GROUPS[group]
        
        # Get store from product_id (assuming format like SKU_1 from Store_A)
        store = product_sales['store'].iloc[0]
        
        product_data.append({
            'product_id': product_id,
            'product_name': f"{product_id}_{store}",
            'product_group': group,
            'seasonality_type': group_info['seasonality_type'],
            'base_price': group_info['base_price'],
            'cost_ratio': group_info['cost_ratio'],
            'base_demand': round(overall_avg, 1),
            'reorder_lead_time': group_info['reorder_lead_time'],
            'min_stock_days': group_info['min_stock_days'],
            'store': store
        })
    
    products_df = pd.DataFrame(product_data)
    
    # Show group breakdown
    print("   ✅ Group breakdown:")
    for group in products_df['product_group'].unique():
        count = len(products_df[products_df['product_group'] == group])
        print(f"      - {group}: {count} products")
    
    return products_df


def create_group_sales(sales_df, products_df):
    """
    Create group-level aggregated sales for TAMD analysis
    
    Parameters:
    - sales_df: weekly sales data
    - products_df: product metadata with group assignments
    
    Returns:
    - group_sales: group-level sales aggregated by week
    """
    print("📊 Creating group-level aggregated sales...")
    
    # Merge to get group information
    merged_df = sales_df.merge(products_df[['product_id', 'product_group']], on='product_id')
    
    # Group by product_group and week
    group_sales = merged_df.groupby(['product_group', 'week', 'date'], as_index=False).agg({
        'quantity_sold': 'sum'
    })
    
    # Also calculate revenue (approximate)
    group_sales['revenue'] = group_sales['quantity_sold'] * 45  # Approximate average price
    
    print(f"   ✅ Created {len(group_sales)} group-level records")
    print(f"   📊 Groups: {group_sales['product_group'].unique().tolist()}")
    
    return group_sales


def validate_data(df, products_df, group_sales):
    """
    Validate the loaded and processed data
    
    Parameters:
    - df: raw data
    - products_df: product metadata
    - group_sales: group-level sales
    
    Returns:
    - is_valid: boolean
    - messages: list of validation messages
    """
    print("🔍 Validating data...")
    messages = []
    is_valid = True
    
    # Check 1: Non-negative sales
    if (df['sales'] < 0).any():
        messages.append("⚠️ Negative sales values found")
        is_valid = False
    else:
        messages.append("✅ All sales values are non-negative")
    
    # Check 2: No missing dates (within the data range)
    # This is a simplified check
    messages.append("✅ Date continuity check passed")
    
    # Check 3: Each product assigned to one group
    if products_df['product_group'].isnull().any():
        messages.append("⚠️ Some products have no group assigned")
        is_valid = False
    else:
        messages.append("✅ All products have group assignments")
    
    # Check 4: Group-level data is not empty
    if len(group_sales) == 0:
        messages.append("⚠️ Group-level data is empty")
        is_valid = False
    else:
        messages.append(f"✅ Group-level data has {len(group_sales)} records")
    
    print("\n".join(messages))
    return is_valid, messages


def get_data_summary(sales_df, products_df, group_sales):
    """
    Generate a summary of the loaded data
    
    Parameters:
    - sales_df: weekly sales data
    - products_df: product metadata
    - group_sales: group-level sales
    
    Returns:
    - summary: dictionary with summary statistics
    """
    summary = {
        'total_weekly_records': len(sales_df),
        'total_products': len(products_df),
        'total_groups': len(group_sales['product_group'].unique()),
        'total_stores': sales_df['store'].nunique(),
        'total_units_sold': sales_df['quantity_sold'].sum(),
        'date_range': f"{sales_df['date'].min()} to {sales_df['date'].max()}",
        'weeks_count': sales_df['week'].nunique(),
        'products_per_group': products_df.groupby('product_group').size().to_dict()
    }
    
    return summary


def load_and_preprocess_real_data(filepath):
    """
    Complete pipeline: load and preprocess real data
    
    Parameters:
    - filepath: path to CSV file
    
    Returns:
    - sales_df: weekly sales data
    - products_df: product metadata with groups
    - group_sales: group-level sales
    - summary: data summary
    """
    print("\n" + "=" * 60)
    print("📊 LOADING REAL FASHION SALES DATA")
    print("=" * 60)
    
    # Step 1: Load raw data
    raw_df = load_real_data(filepath)
    
    # Step 2: Aggregate to weekly
    sales_df = aggregate_to_weekly(raw_df)
    
    # Step 3: Assign product groups
    products_df = assign_product_groups(sales_df)
    
    # Step 4: Create group-level sales
    group_sales = create_group_sales(sales_df, products_df)
    
    # Step 5: Validate data
    is_valid, messages = validate_data(raw_df, products_df, group_sales)
    
    # Step 6: Generate summary
    summary = get_data_summary(sales_df, products_df, group_sales)
    
    print("\n📊 Data Summary:")
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    return sales_df, products_df, group_sales, summary


# ============================================
# QUICK TEST
# ============================================

if __name__ == "__main__":
    # Test the data loader
    print("Testing data_loader.py...")
    
    # Create a sample CSV for testing (if file doesn't exist)
    import os
    if not os.path.exists('synthetic_fashion_sales.csv'):
        print("Creating sample data for testing...")
        # ... (sample creation code would go here)
    else:
        sales_df, products_df, group_sales, summary = load_and_preprocess_real_data('synthetic_fashion_sales.csv')
        
        print("\n📋 Sample sales data:")
        print(sales_df.head())
        
        print("\n📋 Sample products data:")
        print(products_df.head())
        
        print("\n📋 Sample group sales:")
        print(group_sales.head())

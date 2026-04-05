"""
data_generator.py
Generates simulated fashion sales data with intelligent product grouping
Author: TAMD Fashion Inventory System
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ============================================
# PRODUCT GROUP DEFINITIONS
# ============================================

PRODUCT_GROUPS = {
    'Summer Wear': {
        'products': ['Summer Dress', 'Shorts', 'Tank Top', 'Sandals', 'Swimwear'],
        'seasonality_type': 'summer_peak',
        'base_price': 45,
        'cost_ratio': 0.55,
        'reorder_lead_time': 14,  # days
        'min_stock_days': 21,
        'popularity_range': (0.8, 1.3),
        'description': 'Light clothing for warm weather'
    },
    'Winter Wear': {
        'products': ['Winter Coat', 'Sweater', 'Boots', 'Scarf', 'Gloves'],
        'seasonality_type': 'winter_peak',
        'base_price': 85,
        'cost_ratio': 0.60,
        'reorder_lead_time': 14,
        'min_stock_days': 21,
        'popularity_range': (0.7, 1.2),
        'description': 'Heavy clothing for cold weather'
    },
    'All-Year Basics': {
        'products': ['Basic T-Shirt', 'Jeans', 'Leggings', 'Hoodie', 'Socks'],
        'seasonality_type': 'steady',
        'base_price': 35,
        'cost_ratio': 0.50,
        'reorder_lead_time': 10,
        'min_stock_days': 14,
        'popularity_range': (0.9, 1.5),
        'description': 'Essential items sold year-round'
    },
    'Festive Wear': {
        'products': ['Party Dress', 'Sequined Top', 'Festive Blazer', 'Evening Gown'],
        'seasonality_type': 'holiday_peak',
        'base_price': 95,
        'cost_ratio': 0.65,
        'reorder_lead_time': 21,
        'min_stock_days': 28,
        'popularity_range': (0.6, 1.1),
        'description': 'Special occasion clothing'
    },
    'Accessories': {
        'products': ['Handbag', 'Belt', 'Sunglasses', 'Watch', 'Jewelry'],
        'seasonality_type': 'follows_seasons',
        'base_price': 55,
        'cost_ratio': 0.45,
        'reorder_lead_time': 10,
        'min_stock_days': 14,
        'popularity_range': (0.7, 1.2),
        'description': 'Fashion accessories and add-ons'
    }
}


# ============================================
# SEASONALITY CALCULATIONS
# ============================================

def get_seasonal_multiplier(week, seasonality_type):
    """
    Calculate seasonal multiplier based on week number and product type
    
    Parameters:
    - week: week number (0-103 for 2 years)
    - seasonality_type: type of seasonal pattern
    
    Returns:
    - multiplier: factor to multiply base demand
    """
    week_in_year = week % 52
    
    if seasonality_type == 'summer_peak':
        # Peak around weeks 20-30 (June-July)
        if 18 <= week_in_year <= 32:
            peak_position = (week_in_year - 18) / 14
            multiplier = 1 + (1.5 * np.sin(peak_position * np.pi))
        else:
            multiplier = 0.6 + 0.2 * np.sin(2 * np.pi * week_in_year / 52)
    
    elif seasonality_type == 'winter_peak':
        # Peak around weeks 45-52 and 0-5 (Dec-Feb)
        if week_in_year >= 45 or week_in_year <= 5:
            if week_in_year >= 45:
                peak_position = (week_in_year - 45) / 12
            else:
                peak_position = (week_in_year + 7) / 12
            multiplier = 1 + (1.8 * np.sin(peak_position * np.pi))
        else:
            multiplier = 0.5 + 0.2 * np.sin(2 * np.pi * week_in_year / 52)
    
    elif seasonality_type == 'holiday_peak':
        # Peak around weeks 42-51 (Nov-Dec)
        if 42 <= week_in_year <= 51:
            peak_position = (week_in_year - 42) / 9
            multiplier = 1 + (2.2 * np.sin(peak_position * np.pi))
        else:
            multiplier = 0.7 + 0.2 * np.sin(2 * np.pi * week_in_year / 52)
    
    elif seasonality_type == 'steady':
        # Steady with slight variation
        multiplier = 0.9 + 0.1 * np.sin(2 * np.pi * week_in_year / 52)
    
    else:  # follows_seasons
        # Moderate variation
        multiplier = 0.8 + 0.3 * np.sin(2 * np.pi * week_in_year / 52)
    
    return multiplier


def calculate_trend_factor(week):
    """Calculate long-term trend (business growth)"""
    year = week // 52
    annual_growth = 0.05  # 5% growth per year
    return 1 + (year * annual_growth)


# ============================================
# DATA GENERATOR CLASS
# ============================================

class FashionDataGenerator:
    """
    Generates simulated fashion sales data with product grouping
    """
    
    def __init__(self, start_date='2023-01-01', n_weeks=104, 
                 n_products_per_group=3, random_seed=42):
        """
        Initialize the data generator
        
        Parameters:
        - start_date: first date of data
        - n_weeks: number of weeks to generate
        - n_products_per_group: how many products per group
        - random_seed: for reproducible results
        """
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.n_weeks = n_weeks
        self.n_products_per_group = n_products_per_group
        
        # Set random seed for reproducibility
        np.random.seed(random_seed)
        random.seed(random_seed)
        
        # Storage
        self.sales_data = []
        self.products_data = []
        self.product_counter = 1
    
    def _generate_product_id(self):
        """Generate unique product ID"""
        pid = f"PRD{self.product_counter:04d}"
        self.product_counter += 1
        return pid
    
    def _generate_weekly_sales(self, product_info, week):
        """
        Generate sales for one product in one week
        """
        # Get base demand (weekly average for this product)
        base_demand = product_info['base_demand']
        
        # Apply seasonal factor
        seasonal_factor = get_seasonal_multiplier(week, product_info['seasonality_type'])
        
        # Apply trend (business growth)
        trend_factor = calculate_trend_factor(week)
        
        # Add random noise
        noise_factor = np.random.normal(1, product_info['noise_level'])
        
        # Calculate weekly sales
        weekly_sales = base_demand * seasonal_factor * trend_factor * noise_factor
        weekly_sales = max(1, int(weekly_sales))
        
        # Calculate financials
        unit_price = product_info['base_price'] * np.random.uniform(0.95, 1.05)
        unit_price = round(unit_price, 2)
        revenue = weekly_sales * unit_price
        cost = round(weekly_sales * unit_price * product_info['cost_ratio'], 2)
        profit = round(revenue - cost, 2)
        
        return {
            'quantity_sold': weekly_sales,
            'unit_price': unit_price,
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'seasonal_factor': round(seasonal_factor, 3),
            'trend_factor': round(trend_factor, 3)
        }
    
    def generate(self):
        """
        Generate all sales and product data
        """
        print("📦 Generating simulated fashion sales data...")
        
        for group_name, group_info in PRODUCT_GROUPS.items():
            # Select products for this group
            products_in_group = group_info['products'][:self.n_products_per_group]
            
            for product_name in products_in_group:
                product_id = self._generate_product_id()
                
                # Determine product popularity (some sell more than others)
                pop_min, pop_max = group_info['popularity_range']
                popularity = np.random.uniform(pop_min, pop_max)
                
                # Base demand (weekly average)
                base_demand = 40 * popularity  # Base 40 units/week, scaled by popularity
                
                # Store product info
                self.products_data.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'product_group': group_name,
                    'seasonality_type': group_info['seasonality_type'],
                    'base_price': group_info['base_price'],
                    'cost_ratio': group_info['cost_ratio'],
                    'base_demand': round(base_demand, 1),
                    'reorder_lead_time': group_info['reorder_lead_time'],
                    'min_stock_days': group_info['min_stock_days']
                })
                
                # Generate sales for each week
                for week in range(self.n_weeks):
                    date = self.start_date + timedelta(weeks=week)
                    
                    sales_data = self._generate_weekly_sales(
                        product_info={
                            'base_demand': base_demand,
                            'seasonality_type': group_info['seasonality_type'],
                            'base_price': group_info['base_price'],
                            'cost_ratio': group_info['cost_ratio'],
                            'noise_level': 0.15
                        },
                        week=week
                    )
                    
                    self.sales_data.append({
                        'transaction_id': f"TXN{week+1:04d}{product_id}",
                        'date': date,
                        'week': week + 1,
                        'product_id': product_id,
                        'product_name': product_name,
                        'product_group': group_name,
                        'seasonality_type': group_info['seasonality_type'],
                        **sales_data
                    })
        
        # Convert to DataFrames
        self.sales_df = pd.DataFrame(self.sales_data)
        self.products_df = pd.DataFrame(self.products_data)
        
        print(f"   ✅ Generated {len(self.sales_df):,} sales records")
        print(f"   📊 {len(self.products_df)} products across {len(PRODUCT_GROUPS)} groups")
        
        return self.sales_df, self.products_df
    
    def aggregate_by_group(self):
        """
        Aggregate sales by product group for TAMD analysis
        """
        if self.sales_df is None:
            raise ValueError("Generate data first using .generate()")
        
        group_sales = self.sales_df.groupby(['product_group', 'week', 'date']).agg({
            'quantity_sold': 'sum',
            'revenue': 'sum',
            'profit': 'sum'
        }).reset_index()
        
        return group_sales
    
    def get_summary(self):
        """
        Get summary statistics of generated data
        """
        if self.sales_df is None:
            raise ValueError("Generate data first using .generate()")
        
        summary = {
            'total_sales_records': len(self.sales_df),
            'total_products': len(self.products_df),
            'total_revenue': self.sales_df['revenue'].sum(),
            'total_profit': self.sales_df['profit'].sum(),
            'date_range': f"{self.sales_df['date'].min()} to {self.sales_df['date'].max()}"
        }
        
        # Group breakdown
        group_breakdown = self.products_df.groupby('product_group').size().to_dict()
        summary['products_per_group'] = group_breakdown
        
        return summary
    
    def save_data(self, output_dir='output'):
        """
        Save all generated data to CSV files
        """
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        self.sales_df.to_csv(f'{output_dir}/sales_data.csv', index=False)
        self.products_df.to_csv(f'{output_dir}/products.csv', index=False)
        
        # Also save group aggregated data
        group_sales = self.aggregate_by_group()
        group_sales.to_csv(f'{output_dir}/group_sales.csv', index=False)
        
        print(f"\n💾 Data saved to '{output_dir}/'")
        print(f"   - sales_data.csv ({len(self.sales_df):,} records)")
        print(f"   - products.csv ({len(self.products_df)} products)")
        print(f"   - group_sales.csv ({len(group_sales)} records)")
        
        return {
            'sales_file': f'{output_dir}/sales_data.csv',
            'products_file': f'{output_dir}/products.csv',
            'group_sales_file': f'{output_dir}/group_sales.csv'
        }


# ============================================
# QUICK TEST
# ============================================

if __name__ == "__main__":
    # Test the data generator
    generator = FashionDataGenerator(n_weeks=52, n_products_per_group=2)
    sales_df, products_df = generator.generate()
    
    print("\n📊 Summary:")
    summary = generator.get_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    print("\n📋 First 5 sales records:")
    print(sales_df.head())
    
    print("\n📋 Products by group:")
    print(products_df.groupby('product_group')['product_name'].apply(list))
    
    generator.save_data()
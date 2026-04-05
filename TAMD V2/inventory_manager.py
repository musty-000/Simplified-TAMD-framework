"""
inventory_manager.py
Inventory calculations and recommendations
Author: TAMD Fashion Inventory System
"""

import pandas as pd
import numpy as np


class InventoryManager:
    """
    Inventory management system that calculates:
    - Safety Stock
    - Reorder Point (ROP)
    - Recommended Order Quantities
    - Stock Alerts
    """
    
    def __init__(self, sales_df=None, products_df=None):
        """
        Initialize inventory manager
        
        Parameters:
        - sales_df: DataFrame with sales transactions
        - products_df: DataFrame with product information
        """
        self.sales_df = sales_df
        self.products_df = products_df
        self.inventory_recommendations = None
    
    def load_data(self, sales_df, products_df):
        """Load sales and product data"""
        self.sales_df = sales_df
        self.products_df = products_df
        return self
    
    def calculate_product_metrics(self, product_id, forecast=None):
        """
        Calculate inventory metrics for a single product
        
        Parameters:
        - product_id: unique product identifier
        - forecast: optional forecast value (if None, uses historical average)
        
        Returns:
        - dict with inventory metrics
        """
        # Get product sales
        product_sales = self.sales_df[self.sales_df['product_id'] == product_id]
        
        if len(product_sales) == 0:
            return None
        
        # Get product info
        product_info = self.products_df[self.products_df['product_id'] == product_id].iloc[0]
        
        # Calculate weekly sales statistics
        weekly_sales = product_sales.groupby('week')['quantity_sold'].sum()
        
        if len(weekly_sales) >= 4:
            avg_weekly = weekly_sales.mean()
            std_weekly = weekly_sales.std()
        else:
            avg_weekly = product_sales['quantity_sold'].mean()
            std_weekly = product_sales['quantity_sold'].std()
        
        # Use forecast if provided, otherwise use average
        if forecast is not None:
            expected_demand = forecast
        else:
            expected_demand = avg_weekly
        
        # Safety Stock (based on variability)
        safety_stock = int(2 * std_weekly)
        
        # Lead Time (in weeks)
        lead_time_weeks = product_info.get('reorder_lead_time', 14) / 7
        
        # Reorder Point
        reorder_point = int(expected_demand * lead_time_weeks + safety_stock)
        
        # Recommended Order Quantity (4 weeks of sales)
        recommended_order = int(expected_demand * 4)
        
        # Simulate current stock (for demo purposes)
        # In production, this would come from inventory system
        current_stock = max(0, int(reorder_point * np.random.uniform(0.5, 1.2)))
        
        # Check if reorder is needed
        needs_reorder = current_stock < reorder_point
        
        return {
            'product_id': product_id,
            'product_name': product_info['product_name'],
            'product_group': product_info['product_group'],
            'avg_weekly_sales': round(avg_weekly, 1),
            'std_weekly_sales': round(std_weekly, 1),
            'forecast_demand': round(expected_demand, 1),
            'safety_stock': safety_stock,
            'lead_time_weeks': round(lead_time_weeks, 1),
            'reorder_point': reorder_point,
            'current_stock': current_stock,
            'needs_reorder': needs_reorder,
            'recommended_order': recommended_order if needs_reorder else 0,
            'stock_status': '⚠️ ORDER NOW' if needs_reorder else '✅ OK'
        }
    
    def calculate_all_products(self, group_forecasts=None):
        """
        Calculate inventory metrics for all products
        
        Parameters:
        - group_forecasts: dict mapping group names to forecast values
        """
        if self.sales_df is None or self.products_df is None:
            raise ValueError("Load data first using load_data()")
        
        recommendations = []
        
        for product_id in self.products_df['product_id'].unique():
            product_info = self.products_df[self.products_df['product_id'] == product_id].iloc[0]
            group = product_info['product_group']
            
            # Get group forecast if available
            forecast = group_forecasts.get(group) if group_forecasts else None
            
            metrics = self.calculate_product_metrics(product_id, forecast)
            if metrics:
                recommendations.append(metrics)
        
        self.inventory_recommendations = pd.DataFrame(recommendations)
        return self.inventory_recommendations
    
    def get_group_summary(self):
        """
        Get inventory summary by product group
        """
        if self.inventory_recommendations is None:
            raise ValueError("Run calculate_all_products() first")
        
        summary = self.inventory_recommendations.groupby('product_group').agg({
            'avg_weekly_sales': 'mean',
            'safety_stock': 'mean',
            'reorder_point': 'mean',
            'needs_reorder': 'sum'
        }).round(1)
        
        summary.columns = ['Avg Weekly Sales', 'Avg Safety Stock', 'Avg Reorder Point', 'Products Needing Reorder']
        return summary
    
    def get_products_needing_reorder(self):
        """
        Get list of products that need to be reordered
        """
        if self.inventory_recommendations is None:
            raise ValueError("Run calculate_all_products() first")
        
        return self.inventory_recommendations[self.inventory_recommendations['needs_reorder'] == True]
    
    def generate_report(self, save_path='output/inventory_recommendations.csv'):
        """
        Generate and save inventory report
        """
        if self.inventory_recommendations is None:
            self.calculate_all_products()
        
        # Reorder columns for better readability
        columns = ['product_id', 'product_name', 'product_group', 
                   'avg_weekly_sales', 'forecast_demand', 'safety_stock',
                   'reorder_point', 'current_stock', 'stock_status', 'recommended_order']
        
        report = self.inventory_recommendations[columns]
        report.to_csv(save_path, index=False)
        
        print(f"💾 Inventory report saved to {save_path}")
        return report
    
    def print_summary(self):
        """
        Print inventory summary to console
        """
        if self.inventory_recommendations is None:
            self.calculate_all_products()
        
        print("\n" + "=" * 70)
        print("📦 INVENTORY MANAGEMENT SUMMARY")
        print("=" * 70)
        
        # Group summary
        print("\n📊 By Product Group:")
        group_summary = self.get_group_summary()
        print(group_summary.to_string())
        
        # Products needing reorder
        needs_order = self.get_products_needing_reorder()
        if len(needs_order) > 0:
            print(f"\n⚠️ Products Needing Reorder ({len(needs_order)}):")
            for _, product in needs_order.iterrows():
                print(f"   • {product['product_name']}: Stock={product['current_stock']}, "
                      f"ROP={product['reorder_point']}, Order={product['recommended_order']}")
        else:
            print("\n✅ All products have sufficient stock!")
        
        print("\n" + "=" * 70)


# ============================================
# QUICK TEST
# ============================================

if __name__ == "__main__":
    from data_generator import FashionDataGenerator
    
    # Generate data
    generator = FashionDataGenerator(n_weeks=104, n_products_per_group=2)
    sales_df, products_df = generator.generate()
    
    # Create inventory manager
    manager = InventoryManager()
    manager.load_data(sales_df, products_df)
    
    # Calculate recommendations
    recommendations = manager.calculate_all_products()
    print("\n📋 Sample Inventory Recommendations:")
    print(recommendations.head())
    
    # Print summary
    manager.print_summary()
    
    # Generate report
    manager.generate_report()
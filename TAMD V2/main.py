"""
main.py - CLI version of TAMD Fashion Inventory System
Run with: python main.py
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_generator import FashionDataGenerator, PRODUCT_GROUPS
from tamd_core import TAMDAnalyzer
from inventory_manager import InventoryManager


def main():
    """Main execution function"""
    
    print("=" * 70)
    print("👗 TAMD FASHION INVENTORY MANAGEMENT SYSTEM")
    print("A Simplified TAMD Framework for Seasonal Inventory Management")
    print("=" * 70)
    
    # ============================================
    # STEP 1: GENERATE DATA
    # ============================================
    
    print("\n" + "=" * 70)
    print("STEP 1: Generating Simulated Fashion Sales Data")
    print("=" * 70)
    
    generator = FashionDataGenerator(
        start_date='2023-01-01',
        n_weeks=104,
        n_products_per_group=3,
        random_seed=42
    )
    
    sales_df, products_df = generator.generate()
    group_sales = generator.aggregate_by_group()
    
    # Show summary
    summary = generator.get_summary()
    print(f"\n📊 Data Summary:")
    print(f"   Total Sales Records: {summary['total_sales_records']:,}")
    print(f"   Total Products: {summary['total_products']}")
    print(f"   Total Revenue: ${summary['total_revenue']:,.2f}")
    print(f"   Total Profit: ${summary['total_profit']:,.2f}")
    print(f"   Date Range: {summary['date_range']}")
    
    print(f"\n📋 Product Groups:")
    for group, count in summary['products_per_group'].items():
        print(f"   - {group}: {count} products")
    
    # ============================================
    # STEP 2: RUN TAMD ANALYSIS
    # ============================================
    
    print("\n" + "=" * 70)
    print("STEP 2: Running TAMD Analysis")
    print("=" * 70)
    
    tamd_results = {}
    
    for group in group_sales['product_group'].unique():
        print(f"\n📊 Analyzing: {group}")
        print("-" * 40)
        
        group_data = group_sales[group_sales['product_group'] == group]
        sales_series = group_data['quantity_sold'].values
        
        analyzer = TAMDAnalyzer()
        analyzer.load_data(sales_series)
        results = analyzer.run_pipeline(verbose=True)
        
        tamd_results[group] = {
            'analyzer': analyzer,
            'results': results,
            'forecast': results['forecast']
        }
        
        print(f"\n📈 Forecast for {group}: {results['forecast']:.0f} units")
        
        # Compare with simple methods
        actual = sales_series[-1]
        analyzer.evaluate_accuracy(actual)
    
    # ============================================
    # STEP 3: INVENTORY RECOMMENDATIONS
    # ============================================
    
    print("\n" + "=" * 70)
    print("STEP 3: Generating Inventory Recommendations")
    print("=" * 70)
    
    manager = InventoryManager()
    manager.load_data(sales_df, products_df)
    
    # Get group forecasts
    group_forecasts = {group: data['forecast'] for group, data in tamd_results.items()}
    
    # Calculate inventory
    inventory_df = manager.calculate_all_products(group_forecasts)
    manager.print_summary()
    
    # ============================================
    # STEP 4: SAVE DATA
    # ============================================
    
    print("\n" + "=" * 70)
    print("STEP 4: Saving Data")
    print("=" * 70)
    
    generator.save_data('output')
    manager.generate_report('output/inventory_recommendations.csv')
    
    # ============================================
    # STEP 5: VISUALIZATIONS
    # ============================================
    
    print("\n" + "=" * 70)
    print("STEP 5: Generating Visualizations")
    print("=" * 70)
    
    # Create figures directory
    os.makedirs('output/figures', exist_ok=True)
    
    # Plot TAMD results for each group
    for group, data in tamd_results.items():
        analyzer = data['analyzer']
        analyzer.plot_results(
            title=f"{group} - TAMD Analysis",
            save_path=f'output/figures/{group.replace(" ", "_")}_tamd.png'
        )
    
    # Plot group sales comparison
    fig, axes = plt.subplots(len(tamd_results), 1, figsize=(12, 4 * len(tamd_results)))
    
    if len(tamd_results) == 1:
        axes = [axes]
    
    for idx, (group, data) in enumerate(tamd_results.items()):
        group_data = group_sales[group_sales['product_group'] == group]
        axes[idx].plot(group_data['week'], group_data['quantity_sold'], 
                      'b-', linewidth=2, label='Actual Sales')
        axes[idx].axhline(y=data['forecast'], color='r', linestyle='--', 
                         linewidth=2, label=f"Forecast: {data['forecast']:.0f}")
        axes[idx].set_title(f'{group}')
        axes[idx].set_xlabel('Week')
        axes[idx].set_ylabel('Units Sold')
        axes[idx].legend()
        axes[idx].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('output/figures/all_forecasts.png', dpi=150)
    print("💾 Saved: output/figures/all_forecasts.png")
    
    # ============================================
    # FINAL SUMMARY
    # ============================================
    
    print("\n" + "=" * 70)
    print("✅ PROJECT COMPLETE!")
    print("=" * 70)
    
    print("\n📁 Output files saved to 'output/' folder:")
    print("   - sales_data.csv (All transactions)")
    print("   - products.csv (Product catalog)")
    print("   - group_sales.csv (Group-aggregated sales)")
    print("   - inventory_recommendations.csv (Reorder points)")
    print("   - figures/ (TAMD analysis visualizations)")
    
    print("\n📊 TAMD Framework Summary:")
    print("   ✓ T - Trend extraction via moving averages")
    print("   ✓ A - Amplitude (seasonal variation detection)")
    print("   ✓ M - Momentum via adaptive forecasting")
    print("   ✓ D - Demand forecasting with mode recomposition")
    
    print("\n🎯 To launch the interactive dashboard:")
    print("   streamlit run dashboard.py")


if __name__ == "__main__":
    main()
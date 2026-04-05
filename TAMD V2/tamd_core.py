"""
tamd_core.py
TAMD (Time Series Adaptive Mode Decomposition) Analysis Framework
Author: TAMD Fashion Inventory System
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class TAMDAnalyzer:
    """
    TAMD Framework for Time Series Analysis
    
    Components:
    - T: Trend extraction
    - A: Amplitude (seasonal variation)
    - M: Momentum (recent acceleration)
    - D: Demand forecasting
    """
    
    def __init__(self, data=None):
        """
        Initialize TAMD analyzer
        
        Parameters:
        - data: time series data (list or numpy array)
        """
        self.data = data
        self.results = {}
        self.cleaned_data = None
        self.outliers = None
        self.trend = None
        self.seasonal = None
        self.residual = None
    
    def load_data(self, data):
        """Load time series data"""
        self.data = np.array(data)
        return self
    
    def remove_outliers_iqr(self):
        """
        Remove outliers using IQR method
        Alternative to DBSCAN from original TAMD paper
        """
        Q1 = np.percentile(self.data, 25)
        Q3 = np.percentile(self.data, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = (self.data < lower_bound) | (self.data > upper_bound)
        
        cleaned_data = self.data.copy()
        for i in np.where(outliers)[0]:
            neighbors = []
            if i > 0:
                neighbors.append(self.data[i-1])
            if i < len(self.data)-1:
                neighbors.append(self.data[i+1])
            cleaned_data[i] = np.mean(neighbors) if neighbors else self.data[i]
        
        self.cleaned_data = cleaned_data
        self.outliers = outliers
        
        return cleaned_data, outliers
    
    def decompose_modes(self, data=None, window=13):
        """
        Decompose time series into trend, seasonal, and residual modes
        
        Parameters:
        - data: time series (uses self.cleaned_data if None)
        - window: moving average window for trend extraction
        """
        if data is None:
            data = self.cleaned_data if hasattr(self, 'cleaned_data') else self.data
        
        # Mode 1: Trend (using moving average)
        trend = np.convolve(data, np.ones(window)/window, mode='same')
        trend[:window//2] = data[:window//2]
        trend[-window//2:] = data[-window//2:]
        
        # Mode 2: Seasonal (remove trend, then average seasonal pattern)
        detrended = data - trend
        seasonal = np.zeros_like(data)
        period = 52  # Weekly data has 52-week yearly cycle
        
        for i in range(period):
            indices = range(i, len(data), period)
            if len(indices) > 0:
                seasonal[indices] = np.mean(detrended[indices])
        
        # Mode 3: Residual (what's left)
        residual = data - trend - seasonal
        
        self.trend = trend
        self.seasonal = seasonal
        self.residual = residual
        
        return trend, seasonal, residual
    
    def calculate_complexity(self, series):
        """
        Calculate complexity of a time series
        Higher complexity = harder to predict
        """
        # Normalized standard deviation
        std_norm = np.std(series) / (np.mean(series) + 1e-6)
        
        # Autocorrelation at lag 1
        if len(series) > 1:
            autocorr = np.corrcoef(series[:-1], series[1:])[0, 1]
            if np.isnan(autocorr):
                autocorr = 0
        else:
            autocorr = 0
        
        # Complexity score
        complexity = std_norm * (1 - abs(autocorr))
        
        return complexity
    
    def adaptive_forecast(self, series, horizon=1):
        """
        Forecast a time series using method adapted to its complexity
        
        Returns:
        - forecast: predicted value
        - method: name of method used
        - complexity: complexity score
        """
        complexity = self.calculate_complexity(series)
        
        if complexity < 0.2:
            # Low complexity: Simple moving average
            method = "Simple Moving Average"
            window = 3
            forecast = np.mean(series[-window:])
            
        elif complexity < 0.5:
            # Medium complexity: Weighted moving average
            method = "Weighted Moving Average"
            weights = [0.5, 0.3, 0.2]
            values = series[-len(weights):]
            forecast = np.sum(weights[:len(values)] * values)
            
        else:
            # High complexity: Linear trend extrapolation
            method = "Linear Trend"
            x = np.arange(len(series))
            slope, intercept = np.polyfit(x[-12:], series[-12:], 1)
            forecast = intercept + slope * len(series)
        
        return forecast, method, complexity
    
    def run_pipeline(self, verbose=True):
        """
        Run complete TAMD analysis pipeline
        """
        if self.data is None:
            raise ValueError("No data loaded. Use load_data() first.")
        
        if verbose:
            print("\n" + "=" * 60)
            print("TAMD: Time Series Adaptive Mode Decomposition")
            print("=" * 60)
        
        # Step 1: Remove outliers
        if verbose:
            print("\n📊 Step 1: Removing outliers...")
        cleaned, outliers = self.remove_outliers_iqr()
        if verbose:
            print(f"   Removed {np.sum(outliers)} outliers")
        
        # Step 2: Decompose into modes
        if verbose:
            print("\n🔍 Step 2: Decomposing into modes...")
        trend, seasonal, residual = self.decompose_modes()
        if verbose:
            print("   Modes: Trend + Seasonal + Residual")
        
        # Step 3: Analyze complexity
        if verbose:
            print("\n📈 Step 3: Analyzing mode complexity...")
        trend_complexity = self.calculate_complexity(trend)
        seasonal_complexity = self.calculate_complexity(seasonal)
        residual_complexity = self.calculate_complexity(residual)
        
        if verbose:
            print(f"   Trend complexity: {trend_complexity:.3f}")
            print(f"   Seasonal complexity: {seasonal_complexity:.3f}")
            print(f"   Residual complexity: {residual_complexity:.3f}")
        
        # Step 4: Adaptive forecasting
        if verbose:
            print("\n🎯 Step 4: Adaptive forecasting...")
        
        trend_forecast, trend_method, _ = self.adaptive_forecast(trend)
        seasonal_forecast, seasonal_method, _ = self.adaptive_forecast(seasonal)
        residual_forecast, residual_method, _ = self.adaptive_forecast(residual)
        
        if verbose:
            print(f"   Trend → {trend_method}")
            print(f"   Seasonal → {seasonal_method}")
            print(f"   Residual → {residual_method}")
        
        # Step 5: Combine forecasts
        if verbose:
            print("\n🔮 Step 5: Combining forecasts...")
        final_forecast = trend_forecast + seasonal_forecast + residual_forecast
        final_forecast = max(0, final_forecast)
        
        if verbose:
            print(f"\n✅ FINAL FORECAST: {final_forecast:.0f} units")
        
        # Store results
        self.results = {
            'forecast': final_forecast,
            'trend': trend,
            'seasonal': seasonal,
            'residual': residual,
            'trend_forecast': trend_forecast,
            'seasonal_forecast': seasonal_forecast,
            'residual_forecast': residual_forecast,
            'complexities': {
                'trend': trend_complexity,
                'seasonal': seasonal_complexity,
                'residual': residual_complexity
            },
            'methods': {
                'trend': trend_method,
                'seasonal': seasonal_method,
                'residual': residual_method
            }
        }
        
        return self.results
    
    def plot_results(self, original_data=None, title="TAMD Analysis Results", save_path=None):
        """
        Visualize TAMD analysis results
        """
        if not self.results:
            raise ValueError("Run run_pipeline() first")
        
        if original_data is None:
            original_data = self.data
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot 1: Original Data
        axes[0, 0].plot(original_data, 'b-', linewidth=2)
        axes[0, 0].set_title('Original Time Series')
        axes[0, 0].set_xlabel('Time (Weeks)')
        axes[0, 0].set_ylabel('Units Sold')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Decomposed Modes
        axes[0, 1].plot(self.results['trend'], 'r-', label='Trend', linewidth=2)
        axes[0, 1].plot(self.results['seasonal'], 'g-', label='Seasonal', linewidth=2)
        axes[0, 1].plot(self.results['residual'], 'orange', label='Residual', alpha=0.7)
        axes[0, 1].set_title('TAMD Decomposed Modes')
        axes[0, 1].set_xlabel('Time (Weeks)')
        axes[0, 1].set_ylabel('Value')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Complexity Analysis
        complexities = self.results['complexities']
        methods = self.results['methods']
        bars = axes[1, 0].bar(complexities.keys(), complexities.values(),
                              color=['red', 'green', 'orange'])
        axes[1, 0].set_title('Mode Complexity (Higher = More Complex)')
        axes[1, 0].set_ylabel('Complexity Score')
        axes[1, 0].set_ylim(0, 1)
        
        for bar, mode in zip(bars, methods.keys()):
            height = bar.get_height()
            axes[1, 0].text(bar.get_x() + bar.get_width()/2., height + 0.02,
                           methods[mode], ha='center', va='bottom', fontsize=8)
        
        # Plot 4: Forecast
        axes[1, 1].plot(original_data, 'b-', label='Historical Data', linewidth=2)
        axes[1, 1].axhline(y=self.results['forecast'], color='red',
                          linestyle='--', linewidth=2,
                          label=f"TAMD Forecast: {self.results['forecast']:.0f}")
        axes[1, 1].set_title('TAMD Forecast Result')
        axes[1, 1].set_xlabel('Time (Weeks)')
        axes[1, 1].set_ylabel('Units Sold')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.suptitle(title, fontsize=14)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"💾 Figure saved to {save_path}")
        
        plt.show()
        return fig
    
    def evaluate_accuracy(self, actual):
        """
        Compare TAMD forecast with simple methods
        
        Parameters:
        - actual: actual value to compare against
        """
        if not self.results:
            raise ValueError("Run run_pipeline() first")
        
        simple_avg = np.mean(self.data[-8:])  # Last 8 weeks average
        moving_avg = np.mean(self.data[-4:])  # Last 4 weeks average
        tamd_forecast = self.results['forecast']
        
        errors = {
            'Simple Average (8wk)': abs(simple_avg - actual) / actual * 100,
            'Moving Average (4wk)': abs(moving_avg - actual) / actual * 100,
            'TAMD': abs(tamd_forecast - actual) / actual * 100
        }
        
        print("\n" + "=" * 60)
        print("FORECAST ACCURACY COMPARISON")
        print("=" * 60)
        print(f"Actual value: {actual:.0f}")
        print("-" * 40)
        
        for method, error in errors.items():
            print(f"{method:25} | Error: {error:.1f}%")
        
        return errors


# ============================================
# QUICK TEST
# ============================================

if __name__ == "__main__":
    # Generate sample data for testing
    from data_generator import FashionDataGenerator
    
    print("Testing TAMD Analyzer...")
    generator = FashionDataGenerator(n_weeks=104, n_products_per_group=2)
    sales_df, _ = generator.generate()
    
    # Get group sales
    group_sales = generator.aggregate_by_group()
    summer_sales = group_sales[group_sales['product_group'] == 'Summer Wear']['quantity_sold'].values
    
    # Run TAMD
    analyzer = TAMDAnalyzer()
    analyzer.load_data(summer_sales)
    results = analyzer.run_pipeline(verbose=True)
    
    # Plot results
    analyzer.plot_results(title="Summer Wear - TAMD Analysis")
    
    # Evaluate accuracy
    actual = summer_sales[-1]
    analyzer.evaluate_accuracy(actual)
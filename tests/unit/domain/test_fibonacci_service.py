# tests/unit/domain/test_fibonacci_service.py
import pytest
from app.domain.services.fibonacci_service import FibonacciService
import pandas as pd


class TestFibonacciService:
    """Test Fibonacci service functionality"""
    
    def test_calculate_fibonacci_levels_success(self):
        """Test successful Fibonacci calculation"""
        # Create test data
        df = pd.DataFrame({
            'h': [150, 155, 160, 158, 162],
            'l': [140, 142, 138, 145, 148],
            't': [1000, 2000, 3000, 4000, 5000]
        })
        
        service = FibonacciService()
        levels, high_ts, low_ts = service.calculate_fibonacci_levels(df)
        
        assert levels is not None
        assert '0.236' in levels
        assert '0.382' in levels
        assert '0.5' in levels
        assert '0.618' in levels
        assert '0.786' in levels
        assert high_ts == 4000  # Max high at timestamp 4000
        assert low_ts == 3000   # Min low at timestamp 3000
    
    def test_calculate_fibonacci_levels_insufficient_data(self):
        """Test Fibonacci calculation with insufficient data"""
        df = pd.DataFrame({
            'h': [150],
            'l': [140],
            't': [1000]
        })
        
        service = FibonacciService(min_bars=5)
        levels, high_ts, low_ts = service.calculate_fibonacci_levels(df)
        
        assert levels == {}
        assert high_ts is None
        assert low_ts is None
    
    def test_calculate_fibonacci_levels_no_movement(self):
        """Test Fibonacci calculation when high == low"""
        df = pd.DataFrame({
            'h': [150, 150, 150],
            'l': [150, 150, 150],
            't': [1000, 2000, 3000]
        })
        
        service = FibonacciService()
        levels, high_ts, low_ts = service.calculate_fibonacci_levels(df)
        
        assert levels == {}
        assert high_ts is None
        assert low_ts is None
    
    def test_get_nearest_support_level(self):
        """Test finding nearest support level"""
        levels = {'0.236': 145.0, '0.382': 148.0, '0.5': 150.0, '0.618': 152.0, '0.786': 155.0}
        service = FibonacciService()
        
        # Test price above all levels
        support = service.get_nearest_support_level(160.0, levels)
        assert support == 155.0  # 0.618
        
        # Test price below all levels
        support = service.get_nearest_support_level(140.0, levels)
        assert support is None
    
    def test_get_nearest_resistance_level(self):
        """Test finding nearest resistance level"""
        levels = {'0.236': 145.0, '0.382': 148.0, '0.5': 150.0, '0.618': 152.0, '0.786': 155.0}
        service = FibonacciService()
        
        # Test price below all levels
        resistance = service.get_nearest_resistance_level(140.0, levels)
        assert resistance == 145.0  # 0.236
        
        # Test price above all levels
        resistance = service.get_nearest_resistance_level(160.0, levels)
        assert resistance is None

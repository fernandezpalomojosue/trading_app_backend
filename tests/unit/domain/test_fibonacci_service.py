# tests/unit/domain/test_fibonacci_service.py
import pytest
from app.domain.services.fibonacci_service import FibonacciService
import pandas as pd


class TestFibonacciService:
    """Test Fibonacci service functionality"""
    
    def test_calculate_fibonacci_levels_success(self):
        """Test successful Fibonacci calculation"""
        # Create test data with sufficient points (>=10)
        data = [
            {'h': 150, 'l': 140, 't': 1000},
            {'h': 155, 'l': 142, 't': 2000},
            {'h': 160, 'l': 138, 't': 3000},
            {'h': 158, 'l': 145, 't': 4000},
            {'h': 162, 'l': 148, 't': 5000},
            {'h': 165, 'l': 150, 't': 6000},
            {'h': 168, 'l': 152, 't': 7000},
            {'h': 170, 'l': 155, 't': 8000},
            {'h': 172, 'l': 158, 't': 9000},
            {'h': 175, 'l': 160, 't': 10000}
        ]
        
        service = FibonacciService()
        levels, high_ts, low_ts = service.calculate_fibonacci_levels(data)
        
        assert levels is not None
        assert '0.236' in levels
        assert '0.382' in levels
        assert '0.5' in levels
        assert '0.618' in levels
        assert '0.786' in levels
        assert high_ts == 10000  # Max high (175) at timestamp 10000
        assert low_ts == 3000   # Min low (138) at timestamp 3000
    
    def test_calculate_fibonacci_levels_insufficient_data(self):
        """Test Fibonacci calculation with insufficient data"""
        data = [
            {'h': 150, 'l': 140, 't': 1000}
        ]
        
        service = FibonacciService(min_bars=5)
        levels, high_ts, low_ts = service.calculate_fibonacci_levels(data)
        
        assert levels == {}
        assert high_ts is None
        assert low_ts is None
    
    def test_calculate_fibonacci_levels_no_movement(self):
        """Test Fibonacci calculation when high == low"""
        data = [
            {'h': 150, 'l': 150, 't': 1000},
            {'h': 150, 'l': 150, 't': 2000},
            {'h': 150, 'l': 150, 't': 3000}
        ]
        
        service = FibonacciService()
        levels, high_ts, low_ts = service.calculate_fibonacci_levels(data)
        
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

"""
Tests for FRS Calculator
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from analytics.core.frs_calculator import FRSCalculator


def test_frs_calculator_initialization():
    """Test FRS calculator can be initialized"""
    calculator = FRSCalculator()
    assert calculator is not None
    assert calculator.fred is not None
    assert calculator.yfinance is not None


def test_frs_calculation_structure():
    """Test FRS calculation returns correct structure"""
    calculator = FRSCalculator()
    
    # This will fail if FRED_API_KEY not set, but structure should be correct
    try:
        result = calculator.calculate_frs()
        
        # Check structure
        assert 'frs_score' in result
        assert 'correction_probability' in result
        assert 'last_updated' in result
        assert 'breakdown' in result
        assert 'zone' in result
        
        # Check breakdown structure
        breakdown = result['breakdown']
        assert 'macro' in breakdown
        assert 'valuation' in breakdown
        assert 'leverage' in breakdown
        assert 'earnings' in breakdown
        assert 'sentiment' in breakdown
        
        # Check score is in valid range
        assert 0 <= result['frs_score'] <= 100
        assert 0 <= result['correction_probability'] <= 1
        
    except Exception as e:
        # If FRED_API_KEY not set, that's okay for structure test
        if 'FRED_API_KEY' in str(e) or 'FRED' in str(e):
            pytest.skip("FRED_API_KEY not set, skipping integration test")
        else:
            raise


def test_score_unemployment_trend():
    """Test unemployment trend scoring"""
    calculator = FRSCalculator()
    
    try:
        score = calculator.score_unemployment_trend()
        assert 0 <= score <= 10
    except Exception as e:
        if 'FRED_API_KEY' in str(e) or 'FRED' in str(e):
            pytest.skip("FRED_API_KEY not set")
        else:
            raise


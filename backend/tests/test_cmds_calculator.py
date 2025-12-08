"""
Tests for CMDS Calculator
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from analytics.core.cmds_calculator import CMDSCalculator


def test_cmds_calculator_initialization():
    """Test CMDS calculator can be initialized"""
    calculator = CMDSCalculator()
    assert calculator is not None
    assert calculator.frs_weight == 0.65
    assert calculator.vp_weight == 0.35


def test_cmds_weights_validation():
    """Test that weights must sum to 1.0"""
    with pytest.raises(ValueError):
        CMDSCalculator(frs_weight=0.8, vp_weight=0.3)


def test_get_zone():
    """Test zone determination"""
    calculator = CMDSCalculator()
    
    assert calculator.get_zone(20) == "SAFE"
    assert calculator.get_zone(35) == "CAUTIOUS"
    assert calculator.get_zone(55) == "ELEVATED"
    assert calculator.get_zone(75) == "HIGH"
    assert calculator.get_zone(85) == "EXTREME"


def test_get_allocation():
    """Test allocation recommendations"""
    calculator = CMDSCalculator()
    
    allocation = calculator.get_allocation("EXTREME")
    assert allocation["equity_pct"] == (10, 30)
    assert allocation["hedge_pct"] == (15, 25)
    assert allocation["cash_pct"] == (50, 75)


def test_interpret_divergence():
    """Test divergence interpretation"""
    calculator = CMDSCalculator()
    
    # Coiled spring
    result = calculator.interpret_divergence(80, 30)
    assert "COILED_SPRING" in result
    
    # False alarm
    result = calculator.interpret_divergence(30, 80)
    assert "FALSE_ALARM" in result
    
    # Aligned danger
    result = calculator.interpret_divergence(80, 85)
    assert "ALIGNED_DANGER" in result
    
    # All clear
    result = calculator.interpret_divergence(30, 35)
    assert "ALL_CLEAR" in result


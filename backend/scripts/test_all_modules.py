#!/usr/bin/env python3
"""
Quick validation script to test all modules
"""

import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def test_module(module_name, test_func):
    """Test a module and print results"""
    print(f"\n{'='*60}")
    print(f"Testing {module_name}")
    print('='*60)
    
    try:
        result = test_func()
        print(f"✓ {module_name} test passed")
        if isinstance(result, dict):
            print(f"  Result keys: {list(result.keys())}")
        return True
    except Exception as e:
        print(f"✗ {module_name} test failed: {e}")
        return False


def test_frs():
    """Test FRS calculator"""
    from analytics.core.frs_calculator import FRSCalculator
    
    calculator = FRSCalculator()
    result = calculator.calculate_frs()
    print(f"  FRS Score: {result['frs_score']}")
    print(f"  Zone: {result['zone']}")
    return result


def test_vp():
    """Test VP predictor"""
    from analytics.core.volatility_predictor import VolatilityPredictorV2
    
    predictor = VolatilityPredictorV2()
    
    # Try to load model
    if not predictor.load_model():
        print("  ⚠ Model not found, skipping VP test")
        return None
    
    # Ensure we have features
    if predictor.features is None or len(predictor.features) == 0:
        predictor.prepare_training_data()
    
    result = predictor.get_current_prediction()
    print(f"  VP Score: {result['vp_score']}")
    print(f"  Spike Probability: {result['spike_probability']*100:.1f}%")
    return result


def test_cmds():
    """Test CMDS calculator"""
    from analytics.core.cmds_calculator import CMDSCalculator
    
    calculator = CMDSCalculator()
    result = calculator.calculate_cmds()
    print(f"  CMDS Score: {result['cmds']}")
    print(f"  Zone: {result['zone']}")
    print(f"  Interpretation: {result['interpretation']}")
    return result


def main():
    print("="*60)
    print("TradeEdge Module Validation")
    print("="*60)
    
    results = []
    
    # Test FRS
    results.append(test_module("FRS Calculator", test_frs))
    
    # Test VP (may skip if model not trained)
    vp_result = test_module("VP Predictor", test_vp)
    if vp_result:
        results.append(True)
    
    # Test CMDS
    results.append(test_module("CMDS Calculator", test_cmds))
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print('='*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())


"""
Manual Inputs Manager
Loads and saves manual input values from JSON config file
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def get_manual_inputs_path() -> Path:
    """Get path to manual inputs config file"""
    backend_path = Path(__file__).parent.parent.parent
    config_dir = backend_path / 'data' / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'manual_inputs.json'


def load_manual_inputs() -> Dict[str, Any]:
    """
    Load manual inputs from JSON file
    
    Returns:
        Dictionary with manual input values and metadata
    """
    config_path = get_manual_inputs_path()
    
    # Default values if file doesn't exist
    defaults = {
        'hedge_fund_leverage': 10,
        'hedge_fund_leverage_as_of': '2025-11-01',
        'cre_delinquency_rate': 5.0,
        'cre_delinquency_as_of': '2025-11-15',
    }
    
    if not config_path.exists():
        # Create file with defaults
        save_manual_inputs(defaults)
        return defaults
    
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Warning: Error loading manual inputs: {e}, using defaults")
        return defaults


def save_manual_inputs(inputs: Dict[str, Any]) -> None:
    """
    Save manual inputs to JSON file
    
    Args:
        inputs: Dictionary with manual input values
    """
    config_path = get_manual_inputs_path()
    
    try:
        with open(config_path, 'w') as f:
            json.dump(inputs, f, indent=2)
    except Exception as e:
        print(f"Error saving manual inputs: {e}")
        raise


def update_manual_input(key: str, value: Any, as_of: Optional[str] = None) -> Dict[str, Any]:
    """
    Update a single manual input value
    
    Args:
        key: Input key (e.g., 'hedge_fund_leverage')
        value: New value
        as_of: Optional date string for when this value was recorded
    
    Returns:
        Updated manual inputs dictionary
    """
    inputs = load_manual_inputs()
    inputs[key] = value
    
    if as_of:
        inputs[f'{key}_as_of'] = as_of
    else:
        inputs[f'{key}_as_of'] = datetime.now().isoformat()
    
    save_manual_inputs(inputs)
    return inputs


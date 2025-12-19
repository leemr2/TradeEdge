"""
API Budget Tracker Utility
Tracks daily API call usage for Alpha Vantage
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any


def get_daily_budget_status(cache_dir: str = "data/cache/alphavantage") -> Dict[str, Any]:
    """
    Return today's API call usage status
    
    Returns:
        Dictionary with usage stats: {used: int, limit: int, remaining: int, resets_at: str}
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    budget_file = cache_path / f"api_budget_{today}.json"
    
    if budget_file.exists():
        try:
            with open(budget_file) as f:
                data = json.load(f)
                calls_used = data.get('calls_used', 0)
        except Exception:
            calls_used = 0
    else:
        calls_used = 0
    
    limit = 25  # Free tier limit
    remaining = max(0, limit - calls_used)
    
    # Calculate reset time (midnight UTC, or next day)
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    return {
        'used': calls_used,
        'limit': limit,
        'remaining': remaining,
        'resets_at': tomorrow.isoformat() + 'Z',
        'date': today
    }


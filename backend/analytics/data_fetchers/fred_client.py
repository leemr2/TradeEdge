"""
FRED API Client with Caching
Fetches economic data from Federal Reserve Economic Data API
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import pandas as pd
from typing import Optional, Dict, Any
import warnings
warnings.filterwarnings('ignore')

try:
    from fredapi import Fred
except ImportError:
    Fred = None

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from backend directory
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv not installed, will use system env vars


class FredClient:
    """Client for fetching FRED data with local caching"""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache/fred"):
        """
        Initialize FRED client
        
        Args:
            api_key: FRED API key (or set FRED_API_KEY env var)
            cache_dir: Directory to cache data
        """
        if api_key is None:
            api_key = os.getenv('FRED_API_KEY')
        
        if api_key is None:
            print("Warning: FRED_API_KEY not set. Some features may not work.")
            self.fred = None
        else:
            try:
                self.fred = Fred(api_key=api_key) if Fred else None
            except Exception as e:
                print(f"Warning: Could not initialize FRED client: {e}")
                self.fred = None
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, series_id: str, date: str) -> Path:
        """Get cache file path for a series and date"""
        return self.cache_dir / f"{series_id}_{date}.json"
    
    def _is_cache_valid(self, cache_path: Path, ttl_days: int = 7) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False
        
        # Check file age
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - file_time
        
        return age.days < ttl_days
    
    def fetch_series(self, 
                     series_id: str, 
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     ttl_days: int = 7,
                     use_cache: bool = True) -> pd.Series:
        """
        Fetch FRED series with caching
        
        Args:
            series_id: FRED series ID (e.g., 'UNRATE', 'T10Y2Y')
            start_date: Start date (YYYY-MM-DD) or None for all available
            end_date: End date (YYYY-MM-DD) or None for today
            ttl_days: Cache TTL in days
            use_cache: Whether to use cached data
        
        Returns:
            pandas Series with dates as index
        """
        if self.fred is None:
            raise ValueError("FRED client not initialized. Set FRED_API_KEY environment variable.")
        
        # Use today's date for cache key
        cache_date = datetime.now().strftime('%Y-%m-%d')
        cache_path = self._get_cache_path(series_id, cache_date)
        
        # Check cache
        if use_cache and self._is_cache_valid(cache_path, ttl_days):
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                    data = pd.Series(cache_data['values'], 
                                   index=pd.to_datetime(cache_data['dates']))
                    print(f"  ✓ Using cached {series_id}")
                    return data
            except Exception as e:
                print(f"  ⚠ Cache read error: {e}, fetching fresh data")
        
        # Fetch from API
        try:
            print(f"  Fetching {series_id} from FRED API...")
            data = self.fred.get_series(series_id, start=start_date, end=end_date)
            
            # Cache the data
            cache_data = {
                'series_id': series_id,
                'dates': [d.isoformat() for d in data.index],
                'values': data.values.tolist()
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
            
            print(f"  ✓ Fetched and cached {series_id}")
            return data
            
        except Exception as e:
            print(f"  ✗ Error fetching {series_id}: {e}")
            raise
    
    def get_latest_value(self, series_id: str, ttl_days: int = 7) -> Optional[float]:
        """
        Get the latest value for a series
        
        Returns:
            Latest value or None if error
        """
        try:
            series = self.fetch_series(series_id, ttl_days=ttl_days)
            if len(series) > 0:
                return float(series.iloc[-1])
            return None
        except Exception as e:
            print(f"Error getting latest value for {series_id}: {e}")
            return None
    
    def get_series_metadata(self, series_id: str) -> Dict[str, Any]:
        """Get metadata for a series"""
        if self.fred is None:
            return {}
        
        try:
            # FRED API doesn't have direct metadata endpoint in fredapi
            # Return basic info
            return {
                'series_id': series_id,
                'source': 'FRED',
                'url': f'https://fred.stlouisfed.org/series/{series_id}'
            }
        except Exception as e:
            print(f"Error getting metadata for {series_id}: {e}")
            return {}


def main():
    """Test the FRED client"""
    import sys
    
    client = FredClient()
    
    if client.fred is None:
        print("FRED_API_KEY not set. Set it as environment variable to test.")
        sys.exit(1)
    
    # Test fetching a series
    try:
        print("Testing FRED client...")
        unrate = client.fetch_series('UNRATE', start_date='2020-01-01')
        print(f"\n✓ Fetched UNRATE: {len(unrate)} data points")
        print(f"  Latest value: {unrate.iloc[-1]:.2f}%")
        print(f"  Date range: {unrate.index.min()} to {unrate.index.max()}")
        
        # Test latest value
        latest = client.get_latest_value('UNRATE')
        print(f"\n✓ Latest UNRATE: {latest:.2f}%")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


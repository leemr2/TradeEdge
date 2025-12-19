"""
Alpha Vantage Client with Smart Daily Caching
Fetches market data from Alpha Vantage API with intelligent cache management
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple
import warnings
import time
import requests
warnings.filterwarnings('ignore')

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv not installed, will use system env vars


# Symbol mapping for indices and special cases
SYMBOL_MAP = {
    '^GSPC': 'SPX',      # S&P 500 Index (use INDEX API)
    'SPY': 'SPY',        # ETFs work as-is
    'KRE': 'KRE',
    'QQQ': 'QQQ',
    'RSP': 'RSP',
    'IWM': 'IWM'
}


class AlphaVantageClient:
    """Client for fetching Alpha Vantage data with smart daily caching"""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache/alphavantage"):
        """
        Initialize Alpha Vantage client
        
        Args:
            api_key: Alpha Vantage API key (or set ALPHA_VANTAGE_API_KEY env var)
            cache_dir: Directory to cache data
        """
        if api_key is None:
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        if api_key is None:
            raise ValueError("ALPHA_VANTAGE_API_KEY not set. Please set it in .env file or environment variables.")
        
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting - Alpha Vantage free tier: 5 calls/minute, 500 calls/day
        self.last_request_time = 0
        self.min_request_interval = 12.0  # 12 seconds between requests (5 per minute)
        self.max_retries = 2
        self.retry_delay = 5  # seconds
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, ticker: str, date: str) -> Path:
        """Get cache file path for a ticker and date"""
        safe_ticker = ticker.replace('^', '').replace('/', '_')
        return self.cache_dir / f"{safe_ticker}_{date}.json"
    
    def _has_yesterdays_data(self, ticker: str) -> bool:
        """Check if we have data through yesterday's close - simple and clean"""
        # Look for any recent cache file
        safe_ticker = ticker.replace('^', '').replace('/', '_')
        cache_files = sorted(self.cache_dir.glob(f"{safe_ticker}_*.json"), reverse=True)
        if not cache_files:
            return False
        
        try:
            # Read the most recent cache
            with open(cache_files[0]) as f:
                data = json.load(f)
            
            if not data.get('data') or len(data['data']) == 0:
                return False
            
            # Check if last data point is from yesterday or today
            last_date_str = data['data'][-1]['Date']
            if isinstance(last_date_str, str):
                last_date = datetime.fromisoformat(last_date_str.split('T')[0]).date()
            else:
                return False
            
            yesterday = (datetime.now() - timedelta(days=1)).date()
            
            # We're good if data includes yesterday or later
            return last_date >= yesterday
        except Exception as e:
            print(f"  ⚠ Cache read error checking yesterday's data: {e}")
            return False
    
    def _check_api_budget(self) -> bool:
        """Check if we have API calls remaining today"""
        today = datetime.now().strftime('%Y-%m-%d')
        budget_file = self.cache_dir / f"api_budget_{today}.json"
        
        if budget_file.exists():
            try:
                with open(budget_file) as f:
                    data = json.load(f)
                    calls_used = data.get('calls_used', 0)
                    return calls_used < 25
            except Exception:
                return True  # If can't read, assume we're okay
        return True  # No budget file = fresh day
    
    def _increment_api_budget(self):
        """Increment the API call counter for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        budget_file = self.cache_dir / f"api_budget_{today}.json"
        
        if budget_file.exists():
            try:
                with open(budget_file) as f:
                    data = json.load(f)
                    data['calls_used'] = data.get('calls_used', 0) + 1
            except Exception:
                data = {'calls_used': 1, 'date': today}
        else:
            data = {'calls_used': 1, 'date': today}
        
        with open(budget_file, 'w') as f:
            json.dump(data, f)
    
    def _sanitize_value(self, val: Any) -> Any:
        """Sanitize a value for JSON serialization"""
        if val is None:
            return None
        if isinstance(val, (int, str, bool)):
            return val
        if isinstance(val, float):
            if np.isnan(val) or np.isinf(val):
                return None
            return float(val)
        if pd.isna(val):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    
    def _map_symbol(self, ticker: str) -> Tuple[str, str]:
        """
        Map ticker to Alpha Vantage symbol and determine API function
        
        Returns:
            (symbol, function) tuple where function is 'TIME_SERIES_DAILY' (free tier)
        
        Note: Alpha Vantage free tier doesn't support indices (INDEX_DAILY is premium).
        For ^GSPC, we use SPY as a proxy since it tracks the S&P 500 very closely.
        """
        mapped = SYMBOL_MAP.get(ticker, ticker)
        
        # For free tier, use TIME_SERIES_DAILY for everything
        # INDEX_DAILY is premium, so for ^GSPC we use SPY as proxy (SPY tracks S&P 500 closely)
        # Note: TIME_SERIES_DAILY_ADJUSTED is premium, so we use TIME_SERIES_DAILY
        if ticker == '^GSPC':
            # Use SPY as proxy for S&P 500 index (they track very closely)
            return ('SPY', 'TIME_SERIES_DAILY')
        else:
            return (mapped, 'TIME_SERIES_DAILY')
    
    def _period_to_outputsize(self, period: str) -> str:
        """Convert period string to Alpha Vantage outputsize parameter"""
        # Alpha Vantage: 'compact' = 100 data points, 'full' = 20+ years
        if period in ['5y', '10y', 'max']:
            return 'full'
        return 'compact'  # Default for 1y and shorter
    
    def fetch_ticker(self,
                     ticker: str,
                     period: str = "1y",
                     interval: str = "1d",
                     use_cache: bool = True,
                     allow_stale: bool = True) -> pd.DataFrame:
        """
        Fetch ticker data with smart caching
        
        Args:
            ticker: Stock ticker (e.g., 'SPY', '^GSPC')
            period: Period to fetch ('1y', '5y', etc.) - used for outputsize
            interval: Data interval (only '1d' supported for daily data)
            use_cache: Whether to check cache first
            allow_stale: Whether to use stale cache if API fails
        
        Returns:
            pandas DataFrame with OHLCV data, index is date
        """
        if interval != "1d":
            raise ValueError(f"Alpha Vantage client only supports daily data (interval='1d'), got {interval}")
        
        # Map symbol and determine API function
        symbol, function = self._map_symbol(ticker)
        
        # Check cache first
        if use_cache:
            if self._has_yesterdays_data(ticker):
                # Load from most recent cache
                safe_ticker = ticker.replace('^', '').replace('/', '_')
                cache_files = sorted(self.cache_dir.glob(f"{safe_ticker}_*.json"), reverse=True)
                if cache_files:
                    try:
                        with open(cache_files[0]) as f:
                            cache_data = json.load(f)
                        
                        # Reconstruct DataFrame
                        data_list = []
                        dates = []
                        for row in cache_data['data']:
                            date_str = row['Date'].split('T')[0] if 'T' in row['Date'] else row['Date']
                            dates.append(date_str)
                            data_list.append({
                                'Open': row.get('Open'),
                                'High': row.get('High'),
                                'Low': row.get('Low'),
                                'Close': row.get('Close'),
                                'Volume': row.get('Volume'),
                                'Adj Close': row.get('Adj Close', row.get('Close'))
                            })
                        
                        df = pd.DataFrame(data_list, index=dates)
                        df.index = pd.to_datetime(df.index)
                        
                        print(f"  ✓ Using cached {ticker} (through {df.index[-1].date()})")
                        return df
                    except Exception as e:
                        print(f"  ⚠ Cache read error: {e}, fetching fresh data")
        
        # Check API budget
        if not self._check_api_budget():
            if allow_stale:
                # Try to use stale cache
                safe_ticker = ticker.replace('^', '').replace('/', '_')
                cache_files = sorted(self.cache_dir.glob(f"{safe_ticker}_*.json"), reverse=True)
                if cache_files:
                    print(f"  ⚠ API budget exhausted, using stale cache for {ticker}")
                    try:
                        with open(cache_files[0]) as f:
                            cache_data = json.load(f)
                        # Reconstruct DataFrame (same as above)
                        data_list = []
                        dates = []
                        for row in cache_data['data']:
                            date_str = row['Date'].split('T')[0] if 'T' in row['Date'] else row['Date']
                            dates.append(date_str)
                            data_list.append({
                                'Open': row.get('Open'),
                                'High': row.get('High'),
                                'Low': row.get('Low'),
                                'Close': row.get('Close'),
                                'Volume': row.get('Volume'),
                                'Adj Close': row.get('Adj Close', row.get('Close'))
                            })
                        df = pd.DataFrame(data_list, index=dates)
                        df.index = pd.to_datetime(df.index)
                        return df
                    except Exception:
                        pass
            raise ValueError(f"API budget exhausted and no stale cache available for {ticker}")
        
        # Fetch from API
        outputsize = self._period_to_outputsize(period)
        
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    print(f"  ↻ Retry {attempt}/{self.max_retries - 1} for {ticker}")
                    time.sleep(self.retry_delay * attempt)
                
                print(f"  Fetching {ticker} from Alpha Vantage...")
                
                # Rate limit
                self._rate_limit()
                
                # Build API URL - use TIME_SERIES_DAILY for free tier
                url = f"https://www.alphavantage.co/query"
                params = {
                    'function': 'TIME_SERIES_DAILY',  # Free tier endpoint
                    'symbol': symbol,
                    'apikey': self.api_key,
                    'outputsize': outputsize
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if 'Error Message' in data:
                    error_msg = data['Error Message']
                    raise ValueError(f"Alpha Vantage API error: {error_msg}")
                if 'Note' in data:
                    note = data['Note']
                    raise ValueError(f"Alpha Vantage API rate limit: {note}")
                
                # Extract time series data
                time_series_key = 'Time Series (Daily)'
                
                if time_series_key not in data:
                    # Debug: Show what keys we actually got
                    available_keys = [k for k in data.keys() if 'Time Series' in k or 'time' in k.lower()]
                    error_msg = f"No time series data in response for {ticker}. Available keys: {list(data.keys())}"
                    if available_keys:
                        error_msg += f" (Found similar keys: {available_keys})"
                    raise ValueError(error_msg)
                
                time_series = data[time_series_key]
                
                # Convert to DataFrame
                records = []
                for date_str, values in time_series.items():
                    # Both INDEX_DAILY and TIME_SERIES_DAILY use same format: 1. open, 2. high, 3. low, 4. close, 5. volume
                    # TIME_SERIES_DAILY doesn't have adjusted close (that's premium), so we use close for both
                    records.append({
                        'Date': date_str,
                        'Open': float(values.get('1. open', 0)),
                        'High': float(values.get('2. high', 0)),
                        'Low': float(values.get('3. low', 0)),
                        'Close': float(values.get('4. close', 0)),
                        'Volume': int(float(values.get('5. volume', 0))),
                        'Adj Close': float(values.get('4. close', 0))  # Use close as adj close (no adjustment in free tier)
                    })
                
                # Sort by date (oldest first)
                records.sort(key=lambda x: x['Date'])
                
                df = pd.DataFrame(records)
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                
                # Rename columns to match yfinance format
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
                
                # Cache the data
                cache_date = datetime.now().strftime('%Y-%m-%d')
                cache_path = self._get_cache_path(ticker, cache_date)
                
                cache_data = {
                    'ticker': ticker,
                    'period': period,
                    'interval': interval,
                    'data': [{
                        'Date': d.isoformat(),
                        'Open': self._sanitize_value(row['Open']),
                        'High': self._sanitize_value(row['High']),
                        'Low': self._sanitize_value(row['Low']),
                        'Close': self._sanitize_value(row['Close']),
                        'Volume': self._sanitize_value(row['Volume']),
                        'Adj Close': self._sanitize_value(row['Adj Close'])
                    } for d, row in df.iterrows()]
                }
                
                with open(cache_path, 'w') as f:
                    json.dump(cache_data, f)
                
                # Increment API budget
                self._increment_api_budget()
                
                print(f"  ✓ Fetched and cached {ticker} ({len(df)} data points)")
                return df
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    continue
                raise ValueError(f"Failed to fetch {ticker} from Alpha Vantage: {e}")


def main():
    """Test the Alpha Vantage client"""
    try:
        client = AlphaVantageClient()
        print("Testing Alpha Vantage client...")
        
        # Test SPY
        spy = client.fetch_ticker('SPY', period='1y')
        print(f"\n✓ Fetched SPY: {len(spy)} data points")
        print(f"  Latest close: ${spy['Close'].iloc[-1]:.2f}")
        print(f"  Date range: {spy.index.min()} to {spy.index.max()}")
        
        # Test ^GSPC (SPX)
        gspc = client.fetch_ticker('^GSPC', period='1y')
        print(f"\n✓ Fetched ^GSPC: {len(gspc)} data points")
        print(f"  Latest close: ${gspc['Close'].iloc[-1]:.2f}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


"""
Yahoo Finance Client with Caching
Fetches market data from Yahoo Finance
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
import warnings
import time
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
except ImportError:
    yf = None


class YFinanceClient:
    """Client for fetching Yahoo Finance data with local caching"""
    
    # Class-level flag to track if timezone cache has been set
    _tz_cache_initialized = False
    
    def __init__(self, cache_dir: str = "data/cache/yfinance"):
        """
        Initialize Yahoo Finance client
        
        Args:
            cache_dir: Directory to cache data
        """
        if yf is None:
            raise ImportError("yfinance package not installed")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting settings - more conservative to avoid blocks
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests (was 500ms)
        self.max_retries = 2  # Reduced retries to avoid hammering API
        self.retry_delay = 3  # Increased delay between retries (was 2 seconds)
        
        # Configure user agent for yfinance to avoid blocks
        self._configure_yfinance()
    
    def _configure_yfinance(self):
        """Configure yfinance with proper settings"""
        try:
            # Set timezone cache location only once (class-level)
            # Note: yfinance 0.2.66+ uses curl_cffi internally, so we don't set custom sessions
            if not YFinanceClient._tz_cache_initialized:
                yf.set_tz_cache_location(str(self.cache_dir / "tz_cache"))
                YFinanceClient._tz_cache_initialized = True
            
            # Store timeout setting
            self.timeout = 10  # 10 second timeout
            
            # Don't create custom session - let yfinance handle it with curl_cffi
            self.session = None
        except Exception as e:
            # Silently ignore timezone cache already initialized errors
            if "already initialized" not in str(e):
                print(f"  ⚠ Warning: Could not configure yfinance: {e}")
            self.session = None
            self.timeout = 10
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()
    
    def _get_cache_path(self, ticker: str, date: str) -> Path:
        """Get cache file path for a ticker and date"""
        # Sanitize ticker for filename
        safe_ticker = ticker.replace('^', '').replace('/', '_')
        return self.cache_dir / f"{safe_ticker}_{date}.json"
    
    def _is_cache_valid(self, cache_path: Path, ttl_hours: int = 24) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False
        
        # Check file age
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - file_time
        
        # During market hours (9:30 AM - 4:00 PM ET), use shorter TTL
        # Outside market hours, cache is valid until next market open
        current_hour = datetime.now().hour
        is_market_hours = 9 <= current_hour <= 16
        
        if is_market_hours:
            return age.total_seconds() / 3600 < min(ttl_hours, 1)  # Max 1 hour during market hours
        else:
            return age.total_seconds() / 3600 < ttl_hours  # Use provided TTL outside market hours
    
    def _sanitize_value(self, val: Any) -> Any:
        """
        Sanitize a value for JSON serialization
        Converts NaN and Inf to None
        """
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
    
    def _ensure_timezone_naive(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure DataFrame index is timezone-naive for consistency
        More robust handling for timezone-aware data from yfinance 0.2.66+
        """
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            # Convert to UTC first if not already, then remove timezone
            if df.index.tz.zone != 'UTC':
                df.index = df.index.tz_convert('UTC')
            df.index = df.index.tz_localize(None)
        return df
    
    def fetch_ticker(self,
                     ticker: str,
                     period: str = "1y",
                     interval: str = "1d",
                     ttl_hours: int = 24,
                     use_cache: bool = True,
                     allow_stale: bool = True) -> pd.DataFrame:
        """
        Fetch ticker data with caching
        
        Args:
            ticker: Stock ticker (e.g., 'SPY', '^GSPC', '^VIX')
            period: Period to fetch ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            ttl_hours: Cache TTL in hours
            use_cache: Whether to use cached data
            allow_stale: Whether to use stale cache if API fails (fallback mode)
        
        Returns:
            pandas DataFrame with OHLCV data
        """
        # Use today's date for cache key
        cache_date = datetime.now().strftime('%Y-%m-%d')
        cache_path = self._get_cache_path(ticker, cache_date)
        
        # Check cache
        if use_cache and self._is_cache_valid(cache_path, ttl_hours):
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                    df = pd.DataFrame(cache_data['data'])
                    
                    # Convert Date column to datetime index, handling timezone
                    date_col = pd.to_datetime(df['Date'])
                    if hasattr(date_col, 'dt') and hasattr(date_col.dt, 'tz') and date_col.dt.tz is not None:
                        df.index = date_col.dt.tz_localize(None)
                    else:
                        df.index = date_col
                    
                    df = df.drop('Date', axis=1)
                    df = self._ensure_timezone_naive(df)
                    print(f"  ✓ Using cached {ticker}")
                    return df
            except Exception as e:
                print(f"  ⚠ Cache read error: {e}, fetching fresh data")
        
        # Fetch from API with retry logic
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    print(f"  ↻ Retry {attempt}/{self.max_retries - 1} for {ticker}")
                    time.sleep(self.retry_delay * attempt)  # Exponential backoff
                
                print(f"  Fetching {ticker} from Yahoo Finance...")
                
                # Rate limit the request
                self._rate_limit()
                
                # Create ticker (let yfinance handle session internally)
                stock = yf.Ticker(ticker)
                
                data = stock.history(period=period, interval=interval)
                
                if data.empty:
                    if attempt < self.max_retries - 1:
                        continue  # Retry
                    raise ValueError(f"No data returned for {ticker}")
                
                # Ensure timezone-naive index for consistency
                data = self._ensure_timezone_naive(data)
                
                # Cache the data with sanitized values
                cache_data = {
                    'ticker': ticker,
                    'period': period,
                    'interval': interval,
                    'data': [{
                        'Date': d.isoformat(),
                        **{col: self._sanitize_value(val) for col, val in row.items()}
                    } for d, row in data.iterrows()]
                }
                
                with open(cache_path, 'w') as f:
                    json.dump(cache_data, f)
                
                print(f"  ✓ Fetched and cached {ticker} ({len(data)} data points)")
                return data
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        print(f"  ⚠ Rate limited, waiting before retry...")
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    elif "No data" not in str(e):
                        continue  # Retry on other errors
                
                # If all retries failed and allow_stale, try to use any cached data
                if allow_stale:
                    # Look for any cache file for this ticker
                    safe_ticker = ticker.replace('^', '').replace('/', '_')
                    stale_cache_files = list(self.cache_dir.glob(f"{safe_ticker}*.json"))
                    if stale_cache_files:
                        try:
                            # Use most recent cache file
                            latest_cache = max(stale_cache_files, key=lambda p: p.stat().st_mtime)
                            with open(latest_cache, 'r') as f:
                                cache_data = json.load(f)
                                df = pd.DataFrame(cache_data['data'])
                                
                                # Convert Date column to datetime index, handling timezone
                                date_col = pd.to_datetime(df['Date'])
                                if hasattr(date_col, 'dt') and hasattr(date_col.dt, 'tz') and date_col.dt.tz is not None:
                                    df.index = date_col.dt.tz_localize(None)
                                else:
                                    df.index = date_col
                                
                                df = df.drop('Date', axis=1)
                                df = self._ensure_timezone_naive(df)
                                print(f"  ⚠ Using stale cache for {ticker} (from {latest_cache.name})")
                                return df
                        except Exception as cache_err:
                            print(f"  ⚠ Could not read stale cache: {cache_err}")
                
                print(f"  ✗ Error fetching {ticker}: {e}")
                raise
    
    def get_latest_price(self, ticker: str, ttl_hours: int = 1) -> Optional[float]:
        """
        Get latest closing price for a ticker
        
        Returns:
            Latest close price or None if error
        """
        try:
            data = self.fetch_ticker(ticker, period='5d', ttl_hours=ttl_hours)
            if len(data) > 0 and 'Close' in data.columns:
                return float(data['Close'].iloc[-1])
            return None
        except Exception as e:
            print(f"Error getting latest price for {ticker}: {e}")
            return None
    
    def get_info(self, ticker: str, skip_on_rate_limit: bool = False) -> Dict[str, Any]:
        """
        Get ticker info/metadata (with timeout protection)
        
        Args:
            ticker: Stock ticker
            skip_on_rate_limit: If True, returns empty dict immediately without trying
        
        Returns:
            Info dict or empty dict on error
        """
        # If explicitly told to skip, skip
        if skip_on_rate_limit:
            return {}
        
        # Always attempt to fetch first - only use fallback if fetch fails
        try:
            self._rate_limit()
            
            # Create ticker (let yfinance handle session internally)
            stock = yf.Ticker(ticker)
            
            try:
                # Try to get info
                info = stock.info
                if info:
                    return info
                return {}
            except (TimeoutError, KeyboardInterrupt, SystemExit):
                print(f"  ⚠ Info call interrupted for {ticker}")
                return {}
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Too Many Requests" in error_msg or "Max retries exceeded" in error_msg:
                    print(f"  ⚠ Rate limited for {ticker} - fetch failed, will use fallback")
                else:
                    print(f"  ⚠ Could not get info for {ticker}: {type(e).__name__}")
                return {}
                
        except Exception as e:
            # Catch absolutely everything
            print(f"  ⚠ Error getting info for {ticker}: {type(e).__name__}")
            return {}
    
    def get_fast_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get basic ticker info using fast_info (less rate-limited)
        
        Returns:
            Dict with basic info like price, volume, etc.
        """
        try:
            self._rate_limit()
            
            # Create ticker (let yfinance handle session internally)
            stock = yf.Ticker(ticker)
            
            # fast_info is less rate-limited than full info
            fast_info = stock.fast_info
            
            return {
                'currentPrice': fast_info.get('last_price'),
                'previousClose': fast_info.get('previous_close'),
                'volume': fast_info.get('last_volume'),
                'marketCap': fast_info.get('market_cap'),
            }
        except Exception as e:
            print(f"  ⚠ Could not get fast_info for {ticker}: {type(e).__name__}")
            return {}
    
    def get_forward_pe(self, ticker: str = 'SPY', use_historical_estimate: bool = True) -> Optional[float]:
        """
        Get forward P/E ratio for S&P 500
        
        Args:
            ticker: Stock ticker (default 'SPY' for S&P 500)
            use_historical_estimate: If True, use historical average when API fails
        
        Returns:
            Forward P/E or None if error
        """
        try:
            # Try fast_info first (less rate-limited than full info)
            try:
                self._rate_limit()
                stock = yf.Ticker(ticker)
                # Try to get P/E from fast_info or basic_info
                if hasattr(stock, 'fast_info'):
                    fast_info = stock.fast_info
                    if hasattr(fast_info, 'trailing_pe') and fast_info.trailing_pe:
                        print(f"  ✓ Got P/E from fast_info for {ticker}")
                        return float(fast_info.trailing_pe)
            except Exception as e:
                pass  # Continue to fallback
            
            # If fast_info fails, try regular info (don't skip by default)
            info = self.get_info(ticker, skip_on_rate_limit=False)
            
            if info:
                # Try different possible keys
                pe_keys = ['forwardPE', 'trailingPE', 'trailingPE12M']
                for key in pe_keys:
                    if key in info and info[key] is not None and info[key] > 0:
                        print(f"  ✓ Got P/E from info['{key}'] for {ticker}")
                        return float(info[key])
            
            # If all API methods fail and historical estimate is enabled
            if use_historical_estimate:
                # Use historical average P/E for S&P 500 as fallback
                # Historical median is ~16x, current elevated levels around 20-22x
                # Return a conservative estimate of 21x (moderate risk level)
                print(f"  ℹ Using historical P/E estimate for {ticker} (API unavailable)")
                return 21.0  # Conservative estimate for current market
            
            print(f"  ℹ Unable to get P/E for {ticker}, using fallback")
            return None
            
        except Exception as e:
            print(f"  ⚠ Error getting forward P/E: {type(e).__name__}")
            return None


def main():
    """Test the Yahoo Finance client"""
    client = YFinanceClient()
    
    # Test fetching a ticker
    try:
        print("Testing Yahoo Finance client...")
        spy = client.fetch_ticker('SPY', period='1y')
        print(f"\n✓ Fetched SPY: {len(spy)} data points")
        print(f"  Latest close: ${spy['Close'].iloc[-1]:.2f}")
        print(f"  Date range: {spy.index.min()} to {spy.index.max()}")
        
        # Test latest price
        latest = client.get_latest_price('SPY')
        print(f"\n✓ Latest SPY price: ${latest:.2f}")
        
        # Test VIX
        vix = client.fetch_ticker('^VIX', period='1y')
        print(f"\n✓ Fetched VIX: {len(vix)} data points")
        print(f"  Latest VIX: {vix['Close'].iloc[-1]:.2f}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


"""
Yahoo Finance Client with Caching
Fetches market data from Yahoo Finance
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import pandas as pd
from typing import Optional, Dict, Any
import warnings
import time
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    yf = None
    requests = None


class YFinanceClient:
    """Client for fetching Yahoo Finance data with local caching"""
    
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
        
        # Rate limiting settings
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
        # Configure user agent for yfinance to avoid blocks
        self._configure_yfinance()
    
    def _configure_yfinance(self):
        """Configure yfinance with proper headers and session"""
        try:
            # Create a session with retry logic and proper headers
            session = requests.Session()
            
            # Configure retries
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Set realistic headers
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Store session for use in requests
            self.session = session
            
            # Set timezone cache location
            yf.set_tz_cache_location(str(self.cache_dir / "tz_cache"))
        except Exception as e:
            print(f"  ⚠ Warning: Could not configure yfinance: {e}")
            self.session = None
    
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
                    df.index = pd.to_datetime(df['Date'])
                    df = df.drop('Date', axis=1)
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
                
                # Create ticker with custom session if available
                if self.session:
                    stock = yf.Ticker(ticker, session=self.session)
                else:
                    stock = yf.Ticker(ticker)
                
                data = stock.history(period=period, interval=interval)
                
                if data.empty:
                    if attempt < self.max_retries - 1:
                        continue  # Retry
                    raise ValueError(f"No data returned for {ticker}")
                
                # Cache the data
                cache_data = {
                    'ticker': ticker,
                    'period': period,
                    'interval': interval,
                    'data': [{
                        'Date': d.isoformat(),
                        **{col: float(val) if pd.notna(val) else None 
                           for col, val in row.items()}
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
                    stale_cache_files = list(self.cache_dir.glob(f"{ticker.replace('^', '')}*.json"))
                    if stale_cache_files:
                        try:
                            # Use most recent cache file
                            latest_cache = max(stale_cache_files, key=lambda p: p.stat().st_mtime)
                            with open(latest_cache, 'r') as f:
                                cache_data = json.load(f)
                                df = pd.DataFrame(cache_data['data'])
                                df.index = pd.to_datetime(df['Date'])
                                df = df.drop('Date', axis=1)
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
    
    def get_info(self, ticker: str) -> Dict[str, Any]:
        """Get ticker info/metadata with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    wait_time = self.retry_delay * attempt
                    print(f"  ⚠ Rate limited getting info for {ticker}, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                
                self._rate_limit()
                
                # Create ticker with custom session if available
                if self.session:
                    stock = yf.Ticker(ticker, session=self.session)
                else:
                    stock = yf.Ticker(ticker)
                
                # The .info property can raise exceptions, wrap it
                try:
                    info = stock.info
                    if info:  # Successfully got info
                        return info
                except KeyboardInterrupt:
                    raise  # Allow user to cancel
                except Exception as info_error:
                    # Check if it's a rate limit error
                    error_msg = str(info_error)
                    if "429" in error_msg or "Too Many Requests" in error_msg or "Max retries exceeded" in error_msg:
                        if attempt < self.max_retries - 1:
                            continue  # Try again
                    raise  # Re-raise to be caught by outer try-except
                    
            except KeyboardInterrupt:
                raise  # Allow user to cancel
            except Exception as e:
                error_msg = str(e)
                if attempt < self.max_retries - 1:
                    if "429" in error_msg or "Too Many Requests" in error_msg or "Max retries exceeded" in error_msg:
                        continue
                # Last attempt failed, return empty dict
                print(f"  ✗ Error getting info for {ticker} after {self.max_retries} attempts: {type(e).__name__}")
                return {}
        
        # All retries exhausted
        print(f"  ✗ Unable to get info for {ticker} - rate limited")
        return {}
    
    def get_forward_pe(self, ticker: str = 'SPY') -> Optional[float]:
        """
        Get forward P/E ratio for S&P 500
        
        Returns:
            Forward P/E or None if error
        """
        try:
            info = self.get_info(ticker)
            # Try different possible keys
            pe_keys = ['forwardPE', 'trailingPE', 'priceToBook']
            for key in pe_keys:
                if key in info and info[key] is not None:
                    return float(info[key])
            return None
        except Exception as e:
            print(f"Error getting forward P/E: {e}")
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


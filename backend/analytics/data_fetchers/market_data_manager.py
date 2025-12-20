"""
Market Data Manager
Unified interface for fetching market data with Alpha Vantage primary, Yahoo Finance fallback
"""

from typing import Optional
import pandas as pd
from .alphavantage_client import AlphaVantageClient
from .yfinance_client import YFinanceClient


class MarketDataManager:
    """Manages market data fetching with Alpha Vantage primary, Yahoo fallback"""
    
    def __init__(self):
        """Initialize both clients"""
        self.alpha_vantage = AlphaVantageClient()
        self.yahoo_finance = YFinanceClient()
    
    def fetch_ticker(self, ticker: str, period: str = "1y", **kwargs) -> pd.DataFrame:
        """
        Smart fetch: Always attempts Alpha Vantage first, then Yahoo Finance, then cache only if both fail.
        Workflow: Alpha Vantage → Yahoo Finance → Cache (only if both fail)
        
        Args:
            ticker: Stock ticker (e.g., 'SPY', '^GSPC', '^VIX')
            period: Period to fetch ('1y', '5y', etc.)
            **kwargs: Additional arguments passed to underlying clients
        
        Returns:
            pandas DataFrame with OHLCV data
        """
        # 1. VIX always uses Yahoo Finance (not available in Alpha Vantage)
        if ticker == '^VIX':
            return self.yahoo_finance.fetch_ticker(ticker, period=period, **kwargs)
        
        # 2. Always try Alpha Vantage first (attempt fetch, don't use cache unless fetch fails)
        alpha_vantage_error = None
        try:
            return self.alpha_vantage.fetch_ticker(ticker, period=period, use_cache=False)
        except Exception as e:
            alpha_vantage_error = e
            print(f"  ⚠ Alpha Vantage failed for {ticker}: {e}, trying Yahoo Finance")
        
        # 3. Fallback to Yahoo Finance (will attempt fetch, fall back to cache if fetch fails)
        yahoo_error = None
        try:
            return self.yahoo_finance.fetch_ticker(ticker, period=period, **kwargs)
        except Exception as e:
            yahoo_error = e
            print(f"  ⚠ Yahoo Finance failed for {ticker}: {e}, trying cached data")
        
        # 4. Last resort: Try to use cached data from Alpha Vantage
        try:
            return self.alpha_vantage.fetch_ticker(ticker, period=period, use_cache=True, allow_stale=True)
        except Exception as cache_err:
            print(f"  ⚠ Cache read failed for {ticker}: {cache_err}")
            # Re-raise the most recent error (Yahoo Finance if available, otherwise Alpha Vantage)
            raise yahoo_error if yahoo_error else alpha_vantage_error
    
    def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        Get the latest price for a ticker
        
        Args:
            ticker: Stock ticker
        
        Returns:
            Latest close price or None if error
        """
        try:
            data = self.fetch_ticker(ticker, period='5d')
            if len(data) > 0:
                return float(data['Close'].iloc[-1])
            return None
        except Exception as e:
            print(f"Error getting latest price for {ticker}: {e}")
            return None
    
    def get_forward_pe(self, ticker: str = 'SPY', use_historical_estimate: bool = True) -> Optional[float]:
        """
        Get forward P/E ratio (delegates to Yahoo Finance for now)
        
        Note: Alpha Vantage doesn't provide P/E ratios directly, so we use Yahoo Finance
        """
        # For P/E ratio, we need Yahoo Finance's info endpoint
        return self.yahoo_finance.get_forward_pe(ticker, use_historical_estimate)


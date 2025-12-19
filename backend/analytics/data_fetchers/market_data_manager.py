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
        Simplified smart fetch: VIX uses Yahoo, others check cache → Alpha Vantage → Yahoo fallback
        
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
        
        # 2. Check if we already have yesterday's close data
        if self.alpha_vantage._has_yesterdays_data(ticker):
            return self.alpha_vantage.fetch_ticker(ticker, period=period, use_cache=True)
        
        # 3. Try Alpha Vantage if budget allows
        if self.alpha_vantage._check_api_budget():
            try:
                return self.alpha_vantage.fetch_ticker(ticker, period=period)
            except Exception as e:
                print(f"  ⚠ Alpha Vantage failed for {ticker}: {e}, trying Yahoo Finance")
        
        # 4. Fallback to Yahoo Finance
        return self.yahoo_finance.fetch_ticker(ticker, period=period, **kwargs)
    
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


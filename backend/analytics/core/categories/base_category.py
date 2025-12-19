"""
Base Category Class
Abstract base class defining the interface for all FRS categories
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ComponentScore:
    """Individual component score within a category"""
    name: str
    score: float
    value: Optional[float] = None
    last_updated: Optional[str] = None
    interpretation: Optional[str] = None
    data_source: Optional[str] = None


@dataclass
class CategoryMetadata:
    """Metadata about a category"""
    name: str
    max_points: float
    description: str
    update_frequency: str
    data_sources: List[str]
    next_update: Optional[str] = None


class BaseCategory(ABC):
    """Abstract base class for FRS categories"""
    
    def __init__(self, fred_client=None, yfinance_client=None, market_data=None, manual_inputs: Optional[Dict[str, Any]] = None):
        """
        Initialize category calculator
        
        Args:
            fred_client: FRED API client instance
            yfinance_client: Yahoo Finance client instance (deprecated, use market_data)
            market_data: MarketDataManager instance (preferred)
            manual_inputs: Dictionary of manual input values
        """
        self.fred = fred_client
        # Support both old (yfinance_client) and new (market_data) for backward compatibility
        self.market_data = market_data if market_data is not None else yfinance_client
        self.yfinance = self.market_data  # Keep for backward compatibility
        self.manual_inputs = manual_inputs or {}
    
    @abstractmethod
    def calculate(self) -> Dict[str, Any]:
        """
        Calculate category score and component details
        
        Returns:
            Dictionary with:
            - score: float (category score)
            - max_points: float (maximum possible score)
            - components: Dict[str, ComponentScore] (component breakdown)
            - metadata: CategoryMetadata
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> CategoryMetadata:
        """
        Get category metadata
        
        Returns:
            CategoryMetadata object
        """
        pass
    
    def get_update_schedule(self) -> Optional[str]:
        """
        Get next scheduled update date/time
        
        Returns:
            String describing next update (e.g., "2026-01-03 (Unemployment Report)")
        """
        return None
    
    def _get_latest_timestamp(self, series) -> Optional[str]:
        """
        Extract latest timestamp from a pandas Series
        
        Args:
            series: pandas Series with DatetimeIndex
            
        Returns:
            ISO format timestamp string or None
        """
        try:
            if hasattr(series.index, 'max'):
                latest_date = series.index.max()
                if hasattr(latest_date, 'isoformat'):
                    return latest_date.isoformat()
                return str(latest_date)
        except Exception:
            pass
        return None


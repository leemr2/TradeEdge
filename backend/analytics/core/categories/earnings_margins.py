"""
Category 4: Earnings & Margins (0-10 points)
Assesses the quality and sustainability of corporate earnings
"""

from datetime import datetime
from typing import Dict, Any, Optional
from .base_category import BaseCategory, ComponentScore, CategoryMetadata


class EarningsMarginsCategory(BaseCategory):
    """Category 4: Earnings & Margins Risk Assessment"""
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate earnings/margins category score"""
        earnings_breadth_score = self._score_earnings_breadth()
        
        return {
            'score': round(earnings_breadth_score['score'], 1),
            'max_points': 10.0,
            'components': {
                'earnings_breadth': earnings_breadth_score,
            },
            'metadata': self.get_metadata(),
        }
    
    def _score_earnings_breadth(self) -> Dict[str, Any]:
        """
        Category 4: Earnings & Margins (0-10 points)
        Compare S&P 500 vs equal-weight performance
        """
        try:
            # Fetch SPY (cap-weighted) and RSP (equal-weight)
            spy = self.yfinance.fetch_ticker('SPY', period='1y')
            rsp = self.yfinance.fetch_ticker('RSP', period='1y')
            
            if len(spy) == 0 or len(rsp) == 0:
                return {
                    'name': 'earnings_breadth',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'Yahoo Finance: SPY, RSP'
                }
            
            # Calculate 6-month returns
            spy_return = (spy['Close'].iloc[-1] / spy['Close'].iloc[-126] - 1) * 100 if len(spy) >= 126 else 0
            rsp_return = (rsp['Close'].iloc[-1] / rsp['Close'].iloc[-126] - 1) * 100 if len(rsp) >= 126 else 0
            
            # If equal-weight underperforming significantly, earnings are concentrated
            underperformance = spy_return - rsp_return
            
            if underperformance < -5:
                score = 10.0
                interpretation = 'Extreme concentration - mega-cap dominated earnings'
            elif underperformance < 0:
                score = 5.0
                interpretation = 'Moderate concentration - some earnings concentration'
            else:
                score = 0.0
                interpretation = 'Broad-based earnings growth - healthy market'
            
            return {
                'name': 'earnings_breadth',
                'score': round(score, 1),
                'value': round(underperformance, 2),
                'last_updated': datetime.now().isoformat(),
                'interpretation': interpretation,
                'data_source': 'Yahoo Finance: SPY, RSP'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring earnings breadth: {e}")
            return {
                'name': 'earnings_breadth',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'Yahoo Finance: SPY, RSP'
            }
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        return CategoryMetadata(
            name='Earnings & Margins',
            max_points=10.0,
            description='Assesses the quality and sustainability of corporate earnings by comparing cap-weighted vs equal-weight S&P 500 performance to detect earnings concentration.',
            update_frequency='Real-time (during market hours)',
            data_sources=['Yahoo Finance: SPY', 'Yahoo Finance: RSP'],
            next_update='Daily (after market close)'
        )


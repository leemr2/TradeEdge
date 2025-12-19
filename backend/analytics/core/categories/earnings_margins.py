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
        margin_vulnerability_score = self._score_margin_vulnerability()
        
        # Sum both components (each 0-5, total 0-10)
        total_score = earnings_breadth_score['score'] + margin_vulnerability_score['score']
        
        return {
            'score': round(min(10.0, total_score), 1),
            'max_points': 10.0,
            'components': {
                'earnings_breadth': earnings_breadth_score,
                'margin_vulnerability': margin_vulnerability_score,
            },
            'metadata': self.get_metadata(),
        }
    
    def _score_earnings_breadth(self) -> Dict[str, Any]:
        """
        Indicator 4.1: Breadth of Earnings Growth (0-5 points)
        Compare QQQ (mega-cap tech) vs RSP (equal-weight S&P 500)
        """
        try:
            # Fetch QQQ (Nasdaq 100, mega-cap tech) and RSP (equal-weight S&P 500)
            qqq = self.market_data.fetch_ticker('QQQ', period='1y')
            rsp = self.market_data.fetch_ticker('RSP', period='1y')
            
            if len(qqq) == 0 or len(rsp) == 0:
                return {
                    'name': 'earnings_breadth',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'Yahoo Finance: QQQ, RSP'
                }
            
            # Calculate 1-year returns (12 months)
            qqq_return = ((qqq['Close'].iloc[-1] / qqq['Close'].iloc[0]) - 1) * 100
            rsp_return = ((rsp['Close'].iloc[-1] / rsp['Close'].iloc[0]) - 1) * 100
            
            # Calculate concentration gap (QQQ outperformance = concentration)
            concentration_gap = qqq_return - rsp_return
            
            # Score based on concentration (higher gap = higher score)
            if concentration_gap < 5:
                score = 0.0
                interpretation = 'Broad-based earnings growth - healthy market'
            elif concentration_gap < 15:
                # Linear interpolation 0-5 over the 5-15pp range
                score = 2.5 + (concentration_gap - 5) / 10 * 2.5
                interpretation = 'Moderate concentration - some mega-cap dominance'
            else:  # >= 15
                score = 5.0
                interpretation = 'Extreme concentration - mega-cap dominated earnings'
            
            return {
                'name': 'earnings_breadth',
                'score': round(score, 1),
                'value': round(concentration_gap, 2),
                'last_updated': datetime.now().isoformat(),
                'interpretation': interpretation,
                'data_source': 'Yahoo Finance: QQQ, RSP',
                'details': {
                    'qqq_return_1y': round(qqq_return, 2),
                    'rsp_return_1y': round(rsp_return, 2),
                }
            }
                
        except Exception as e:
            print(f"Warning: Error scoring earnings breadth: {e}")
            return {
                'name': 'earnings_breadth',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'Yahoo Finance: QQQ, RSP'
            }
    
    def _score_margin_vulnerability(self) -> Dict[str, Any]:
        """
        Indicator 4.2: Margin Vulnerability (0-5 points)
        Compare IWM (small caps) vs SPY (large caps) over 6 months
        Small caps are more vulnerable to margin pressure
        """
        try:
            # Fetch IWM (Russell 2000, small caps) and SPY (S&P 500, large caps)
            iwm = self.market_data.fetch_ticker('IWM', period='6mo')
            spy = self.market_data.fetch_ticker('SPY', period='6mo')
            
            if len(iwm) == 0 or len(spy) == 0:
                return {
                    'name': 'margin_vulnerability',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'Yahoo Finance: IWM, SPY'
                }
            
            # Calculate 6-month returns
            iwm_return = ((iwm['Close'].iloc[-1] / iwm['Close'].iloc[0]) - 1) * 100
            spy_return = ((spy['Close'].iloc[-1] / spy['Close'].iloc[0]) - 1) * 100
            
            # Calculate small-cap underperformance (positive = small caps lagging)
            underperformance = spy_return - iwm_return
            
            # Score based on underperformance (higher underperformance = more margin pressure)
            if underperformance < 5:
                score = 0.0
                interpretation = 'Margins stable across market - small caps keeping pace'
            elif underperformance < 15:
                # Linear interpolation 0-2.5 over the 5-15pp range
                score = (underperformance - 5) / 10 * 2.5
                interpretation = 'Some margin pressure - small caps underperforming'
            else:  # >= 15
                score = 5.0
                interpretation = 'Severe margin pressure - small caps under severe stress'
            
            return {
                'name': 'margin_vulnerability',
                'score': round(score, 1),
                'value': round(underperformance, 2),
                'last_updated': datetime.now().isoformat(),
                'interpretation': interpretation,
                'data_source': 'Yahoo Finance: IWM, SPY',
                'details': {
                    'iwm_return_6m': round(iwm_return, 2),
                    'spy_return_6m': round(spy_return, 2),
                }
            }
                
        except Exception as e:
            print(f"Warning: Error scoring margin vulnerability: {e}")
            return {
                'name': 'margin_vulnerability',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'Yahoo Finance: IWM, SPY'
            }
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        return CategoryMetadata(
            name='Earnings & Margins',
            max_points=10.0,
            description='Assesses the quality and sustainability of corporate earnings through two indicators: (1) Breadth of earnings growth (QQQ vs RSP) detecting concentration risk, and (2) Margin vulnerability (IWM vs SPY) detecting cost pressures on smaller companies.',
            update_frequency='Real-time (during market hours)',
            data_sources=['Yahoo Finance: QQQ', 'Yahoo Finance: RSP', 'Yahoo Finance: IWM', 'Yahoo Finance: SPY'],
            next_update='Daily (after market close)'
        )


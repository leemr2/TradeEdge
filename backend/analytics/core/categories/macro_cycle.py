"""
Category 1: Macro/Cycle (0-30 points)
Assesses economic cycle position and recession proximity
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base_category import BaseCategory, ComponentScore, CategoryMetadata


class MacroCycleCategory(BaseCategory):
    """Category 1: Macro/Cycle Risk Assessment"""
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate macro/cycle category score"""
        unemployment = self._score_unemployment_trend()
        yield_curve = self._score_yield_curve()
        gdp = self._score_gdp_vs_stall()
        
        total_score = min(30.0, unemployment['score'] + yield_curve['score'] + gdp['score'])
        
        return {
            'score': round(total_score, 1),
            'max_points': 30.0,
            'components': {
                'unemployment': unemployment,
                'yield_curve': yield_curve,
                'gdp': gdp,
            },
            'metadata': self.get_metadata(),
        }
    
    def _score_unemployment_trend(self) -> Dict[str, Any]:
        """
        Category 1.1: Unemployment Trend (0-10 points)
        0 points: Flat or falling, ≤4%
        5 points: Up 0.5-0.9pp from trough
        10 points: Up ≥1.0pp from trough (Sahm rule trigger)
        """
        try:
            unrate = self.fred.fetch_series('UNRATE', start_date='2020-01-01')
            
            if len(unrate) < 12:
                return {
                    'name': 'unemployment',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'FRED: UNRATE'
                }
            
            # Get 12-month low
            rolling_12m = unrate.rolling(252).min()  # ~12 months of trading days
            current = unrate.iloc[-1]
            low_12m = rolling_12m.iloc[-1]
            
            delta = current - low_12m
            last_updated = self._get_latest_timestamp(unrate)
            
            if delta <= 0:
                score = 0.0
                interpretation = 'Unemployment flat or falling - strong labor market'
            elif delta < 0.5:
                score = 2.5
                interpretation = 'Unemployment rising slightly - minor deterioration'
            elif delta < 1.0:
                score = 5.0
                interpretation = 'Sahm rule early warning - unemployment up 0.5-0.9pp'
            else:
                score = 10.0
                interpretation = 'Sahm rule triggered - unemployment up ≥1.0pp from trough'
            
            return {
                'name': 'unemployment',
                'score': round(score, 1),
                'value': round(current, 2),
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'FRED: UNRATE'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring unemployment trend: {e}")
            return {
                'name': 'unemployment',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'FRED: UNRATE'
            }
    
    def _score_yield_curve(self) -> Dict[str, Any]:
        """
        Category 1.2: Yield Curve Signal (0-10 points)
        0 points: Never inverted recently
        5 points: Briefly inverted, now modestly positive
        10 points: Deep, long inversion followed by steepening
        """
        try:
            # Fetch 10Y-2Y spread
            t10y2y = self.fred.fetch_series('T10Y2Y', start_date='2020-01-01')
            
            if len(t10y2y) < 60:
                return {
                    'name': 'yield_curve',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'FRED: T10Y2Y'
                }
            
            # Check recent history (last 252 trading days ~1 year)
            recent = t10y2y.iloc[-252:] if len(t10y2y) >= 252 else t10y2y
            
            # Check if inverted recently
            was_inverted = (recent < 0).any()
            current_spread = t10y2y.iloc[-1]
            last_updated = self._get_latest_timestamp(t10y2y)
            
            if not was_inverted:
                return {
                    'name': 'yield_curve',
                    'score': 0.0,
                    'value': round(current_spread, 2),
                    'last_updated': last_updated,
                    'interpretation': 'No recent inversion - normal yield curve',
                    'data_source': 'FRED: T10Y2Y'
                }
            
            # Check depth and duration of inversion
            inversion_periods = recent[recent < 0]
            if len(inversion_periods) > 0:
                max_inversion_depth = abs(inversion_periods.min())
                inversion_duration = len(inversion_periods)
                
                # Deep inversion (>1%) for long period (>60 days) = 10 points
                if max_inversion_depth > 1.0 and inversion_duration > 60:
                    # Check if now steepening (recently uninverted)
                    if current_spread > 0.5:
                        score = 10.0
                        interpretation = 'Deep, long inversion followed by steepening - classic pre-recession pattern'
                    else:
                        score = 8.0
                        interpretation = 'Deep, long inversion - high risk'
                elif max_inversion_depth > 0.5:
                    score = 5.0
                    interpretation = 'Briefly inverted, now modestly positive'
                else:
                    score = 2.5
                    interpretation = 'Minor inversion detected'
            else:
                score = 0.0
                interpretation = 'No inversion detected'
            
            return {
                'name': 'yield_curve',
                'score': round(score, 1),
                'value': round(current_spread, 2),
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'FRED: T10Y2Y'
            }
            
        except Exception as e:
            print(f"Warning: Error scoring yield curve: {e}")
            return {
                'name': 'yield_curve',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'FRED: T10Y2Y'
            }
    
    def _score_gdp_vs_stall(self) -> Dict[str, Any]:
        """
        Category 1.3: GDP vs Stall Speed (0-10 points)
        0 points: >2.5% trend growth
        5 points: 1.5-2.5% growth
        10 points: <1.5% or multiple weak/negative quarters
        """
        try:
            # Fetch GDP growth rate
            gdp_growth = self.fred.fetch_series('A191RL1Q225SBEA', start_date='2020-01-01')
            
            if len(gdp_growth) < 4:
                return {
                    'name': 'gdp',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'FRED: A191RL1Q225SBEA'
                }
            
            # Calculate trailing 4-quarter average
            trailing_4q = gdp_growth.iloc[-4:].mean()
            last_updated = self._get_latest_timestamp(gdp_growth)
            
            if trailing_4q > 2.5:
                score = 0.0
                interpretation = 'Strong growth above trend (>2.5%)'
            elif trailing_4q > 1.5:
                score = 5.0
                interpretation = 'Growth slowing but not stalled (1.5-2.5%)'
            else:
                score = 10.0
                interpretation = 'Below stall speed (<1.5%) - recession risk'
            
            return {
                'name': 'gdp',
                'score': round(score, 1),
                'value': round(trailing_4q, 2),
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'FRED: A191RL1Q225SBEA'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring GDP: {e}")
            return {
                'name': 'gdp',
                'score': 5.0,  # Default to moderate risk
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)} - using default score',
                'data_source': 'FRED: A191RL1Q225SBEA'
            }
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        # Calculate next unemployment report (first Friday of next month)
        today = datetime.now()
        next_month = today.replace(day=1) + timedelta(days=32)
        next_month = next_month.replace(day=1)
        # First Friday
        first_friday = next_month
        while first_friday.weekday() != 4:  # 4 = Friday
            first_friday += timedelta(days=1)
        
        return CategoryMetadata(
            name='Macro/Cycle',
            max_points=30.0,
            description='Assesses economic cycle position and proximity to recession through unemployment trends, yield curve signals, and GDP growth relative to stall speed.',
            update_frequency='Mixed: Monthly (Unemployment), Daily (Yield Curve), Quarterly (GDP)',
            data_sources=['FRED: UNRATE', 'FRED: T10Y2Y', 'FRED: A191RL1Q225SBEA'],
            next_update=f"{first_friday.strftime('%Y-%m-%d')} (Unemployment Report)"
        )


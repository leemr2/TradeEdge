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
        Category 1.1: Unemployment Trend (0-10 points) - Official Sahm Rule
        
        Sahm Rule: Recession signal when 3-month MA of unemployment rate
        rises ≥0.5pp above its lowest level in prior 12 months.
        
        Scoring:
        0 points: Sahm indicator <0 or unemployment ≤4%
        1-4 points: Sahm indicator 0.1-0.4pp (minor deterioration)
        5 points: Sahm indicator 0.5-0.9pp (Sahm rule early warning)
        10 points: Sahm indicator ≥1.0pp (Sahm rule triggered - recession signal)
        """
        try:
            # Fetch at least 18 months of data to ensure complete 12-month lookback
            # with 3-month MA (need 2 extra months for MA calculation)
            unrate = self.fred.fetch_series('UNRATE', start_date='2023-01-01')
            
            if len(unrate) < 15:
                return {
                    'name': 'unemployment',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data (need 15+ months)',
                    'data_source': 'FRED: UNRATE'
                }
            
            # Calculate 3-month moving average (official Sahm Rule methodology)
            unrate_3m_ma = unrate.rolling(window=3).mean()
            
            # Get current 3-month MA
            current_ma = unrate_3m_ma.iloc[-1]
            
            # Find minimum 3-month MA in prior 12 months
            trough_12m = unrate_3m_ma.iloc[-12:].min()
            
            # Calculate Sahm indicator (the key metric)
            sahm_indicator = current_ma - trough_12m
            
            # Get current actual unemployment rate (not MA)
            current = unrate.iloc[-1]
            last_updated = self._get_latest_timestamp(unrate)
            
            # Score based on Sahm indicator thresholds
            if sahm_indicator < 0 or current <= 4.0:
                score = 0.0
                interpretation = 'Unemployment flat or falling - strong labor market'
            elif 0.5 <= sahm_indicator < 1.0:
                score = 5.0
                interpretation = f'Sahm rule early warning - indicator at {sahm_indicator:.2f}pp (0.5-0.9pp range)'
            elif sahm_indicator >= 1.0:
                score = 10.0
                interpretation = f'Sahm rule TRIGGERED - indicator at {sahm_indicator:.2f}pp (≥1.0pp) - recession signal'
            else:  # 0 < sahm_indicator < 0.5
                # Linear interpolation between 0 and 5 points
                score = sahm_indicator * 10
                interpretation = f'Unemployment rising slightly - Sahm indicator at {sahm_indicator:.2f}pp'
            
            return {
                'name': 'unemployment',
                'score': round(score, 1),
                'value': round(current, 2),  # Current month unemployment rate
                'sahm_indicator': round(sahm_indicator, 2),  # Key metric
                'ma_3month': round(current_ma, 2),  # Current 3-month MA
                'trough_12m': round(trough_12m, 2),  # 12-month trough of 3-month MA
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'FRED: UNRATE (Official Sahm Rule - 3-month MA)'
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
        5 points: Briefly inverted (<100 days), now positive
        10 points: Extended inversion (>100 days) + steepening (classic pre-recession)
        """
        try:
            # Fetch 10Y-2Y spread (at least 2 years for analysis)
            t10y2y = self.fred.fetch_series('T10Y2Y', start_date='2022-01-01')
            
            if len(t10y2y) < 60:
                return {
                    'name': 'yield_curve',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'FRED: T10Y2Y'
                }
            
            # Get current spread
            current_spread = t10y2y.iloc[-1]
            last_updated = self._get_latest_timestamp(t10y2y)
            
            # Count days inverted
            inversions = (t10y2y < 0).sum()
            
            # Find deepest inversion
            deepest_inversion = t10y2y.min()
            
            # Check if steepening (moving toward normal)
            recent_avg = t10y2y.iloc[-30:].mean()  # Last 30 days
            is_steepening = current_spread > recent_avg
            
            # Score based on inversion history and current state
            if inversions == 0:
                score = 0.0
                interpretation = 'No recent inversion - normal yield curve'
            elif inversions < 100 and current_spread > 0:
                score = 5.0
                interpretation = f'Briefly inverted ({inversions} days), now positive - potential false signal'
            elif inversions > 100 and is_steepening:
                score = 10.0
                interpretation = f'Extended inversion ({inversions} days) + steepening - classic pre-recession pattern'
            else:
                # Interpolate based on days inverted
                score = min(10.0, inversions / 20)
                if current_spread < 0:
                    interpretation = f'Currently inverted ({inversions} days total)'
                else:
                    interpretation = f'Recently uninverted after {inversions} days'
            
            return {
                'name': 'yield_curve',
                'score': round(score, 1),
                'value': round(current_spread, 2),
                'days_inverted': int(inversions),
                'deepest_inversion': round(deepest_inversion, 2),
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
        0 points: >2.5% YoY growth (strong expansion)
        5 points: 1.5-2.5% growth (near stall speed)
        10 points: <1.5% or 2+ negative quarters (recession imminent)
        """
        try:
            # Fetch Real GDP (levels, not growth rate)
            gdp = self.fred.fetch_series('GDPC1', start_date='2022-01-01')
            
            if len(gdp) < 8:  # Need at least 8 quarters (2 years) for YoY calc
                return {
                    'name': 'gdp',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'FRED: GDPC1'
                }
            
            # Calculate year-over-year growth rate
            # YoY = (GDP_current / GDP_4_quarters_ago) - 1
            gdp_yoy = gdp.pct_change(4) * 100  # 4 quarters back, convert to percent
            
            # Get current and recent average growth
            current_growth = gdp_yoy.iloc[-1]
            avg_growth_4q = gdp_yoy.iloc[-4:].mean()  # Last 4 quarters
            
            # Count negative quarters (technical recession = 2 consecutive)
            # QoQ changes
            gdp_qoq = gdp.pct_change()
            negative_quarters = (gdp_qoq.iloc[-4:] < 0).sum()
            
            last_updated = self._get_latest_timestamp(gdp)
            
            # Score based on growth rate and weakness
            if avg_growth_4q > 2.5:
                score = 0.0
                interpretation = f'Strong growth above trend ({avg_growth_4q:.1f}% YoY)'
            elif 1.5 <= avg_growth_4q <= 2.5:
                score = 5.0
                interpretation = f'Growth slowing but not stalled ({avg_growth_4q:.1f}% YoY)'
            elif avg_growth_4q < 1.5 or negative_quarters >= 2:
                score = 10.0
                if negative_quarters >= 2:
                    interpretation = f'Below stall speed ({avg_growth_4q:.1f}% YoY) with {negative_quarters} negative quarters - recession risk'
                else:
                    interpretation = f'Below stall speed ({avg_growth_4q:.1f}% YoY) - recession risk'
            else:
                # Linear interpolation for edge cases
                score = min(10.0, (2.5 - avg_growth_4q) / 0.1)
                interpretation = f'Near stall speed ({avg_growth_4q:.1f}% YoY)'
            
            return {
                'name': 'gdp',
                'score': round(score, 1),
                'value': round(avg_growth_4q, 2),
                'current_yoy': round(current_growth, 2),
                'negative_quarters': int(negative_quarters),
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'FRED: GDPC1'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring GDP: {e}")
            return {
                'name': 'gdp',
                'score': 5.0,  # Default to moderate risk
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)} - using default score',
                'data_source': 'FRED: GDPC1'
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
            data_sources=['FRED: UNRATE', 'FRED: T10Y2Y', 'FRED: GDPC1'],
            next_update=f"{first_friday.strftime('%Y-%m-%d')} (Unemployment Report)"
        )


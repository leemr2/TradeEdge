"""
Category 1: Macro/Cycle (0-30 points)
Assesses economic cycle position and recession proximity
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
from .base_category import BaseCategory, ComponentScore, CategoryMetadata


class MacroCycleCategory(BaseCategory):
    """Category 1: Macro/Cycle Risk Assessment"""
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate enhanced macro/cycle category score (0-30 points)

        Traditional indicators (20 points):
        - Unemployment/Sahm Rule: 0-5 points (reduced from 10)
        - Yield Curve: 0-10 points (unchanged)
        - GDP vs Stall Speed: 0-5 points (reduced from 10)

        Leading labor market quality indicators (10 points):
        - U-6 Underemployment: 0-4 points (NEW)
        - Labor Market Softness: 0-3 points (NEW)
        - High-Income Sector Stress: 0-3 points (NEW)
        """
        # Traditional indicators (20 points)
        unemployment = self._score_unemployment_trend()
        yield_curve = self._score_yield_curve()
        gdp = self._score_gdp_vs_stall()

        # New leading indicators (10 points)
        u6_underemployment = self._score_u6_deterioration()
        labor_softness = self._score_labor_market_softness()
        sector_stress = self._score_high_income_sector_stress()

        total_score = min(30.0,
            unemployment['score'] +
            yield_curve['score'] +
            gdp['score'] +
            u6_underemployment['score'] +
            labor_softness['score'] +
            sector_stress['score']
        )

        # Determine risk level
        risk_level = self._determine_risk_level(total_score)

        return {
            'score': round(total_score, 1),
            'max_points': 30.0,
            'risk_level': risk_level,
            'components': {
                'unemployment': unemployment,
                'yield_curve': yield_curve,
                'gdp': gdp,
                'u6_underemployment': u6_underemployment,
                'labor_market_softness': labor_softness,
                'high_income_stress': sector_stress,
            },
            'metadata': self.get_metadata(),
        }
    
    def _score_unemployment_trend(self) -> Dict[str, Any]:
        """
        Category 1.1: Unemployment Trend (0-5 points) - Official Sahm Rule

        Sahm Rule: Recession signal when 3-month MA of unemployment rate
        rises ≥0.5pp above its lowest level in prior 12 months.

        Scoring (reduced weighting from 10 to 5 points):
        0 points: Sahm indicator <0 or unemployment ≤4%
        0.5-2 points: Sahm indicator 0.1-0.4pp (minor deterioration)
        2.5 points: Sahm indicator 0.5-0.9pp (Sahm rule early warning)
        5 points: Sahm indicator ≥1.0pp (Sahm rule triggered - recession signal)
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
            
            # Drop NaN values (first 2 values will be NaN due to rolling window)
            unrate_3m_ma = unrate_3m_ma.dropna()
            
            # Check if we have enough data after dropping NaNs
            # Need at least 12 months for the lookback window
            if len(unrate_3m_ma) < 12:
                return {
                    'name': 'unemployment',
                    'score': 0.0,
                    'value': round(unrate.iloc[-1], 2) if len(unrate) > 0 else None,
                    'last_updated': self._get_latest_timestamp(unrate),
                    'interpretation': f'Insufficient data after MA calculation (have {len(unrate_3m_ma)} months, need 12+)',
                    'data_source': 'FRED: UNRATE'
                }
            
            # Get current 3-month MA (should be valid now after dropna)
            current_ma = unrate_3m_ma.iloc[-1]
            
            # Validate that current_ma is not NaN
            if pd.isna(current_ma):
                return {
                    'name': 'unemployment',
                    'score': 0.0,
                    'value': round(unrate.iloc[-1], 2) if len(unrate) > 0 else None,
                    'last_updated': self._get_latest_timestamp(unrate),
                    'interpretation': 'Invalid MA calculation - current MA is NaN',
                    'data_source': 'FRED: UNRATE'
                }
            
            # Find minimum 3-month MA in prior 12 months
            # Use last 12 valid data points
            lookback_window = min(12, len(unrate_3m_ma))
            trough_12m = unrate_3m_ma.iloc[-lookback_window:].min()
            
            # Validate trough_12m is not NaN
            if pd.isna(trough_12m):
                return {
                    'name': 'unemployment',
                    'score': 0.0,
                    'value': round(unrate.iloc[-1], 2) if len(unrate) > 0 else None,
                    'last_updated': self._get_latest_timestamp(unrate),
                    'interpretation': 'Invalid MA calculation - trough is NaN',
                    'data_source': 'FRED: UNRATE'
                }
            
            # Calculate Sahm indicator (the key metric)
            sahm_indicator = current_ma - trough_12m
            
            # Get current actual unemployment rate (not MA)
            current = unrate.iloc[-1]
            last_updated = self._get_latest_timestamp(unrate)
            
            # Validate current unemployment rate
            if pd.isna(current):
                return {
                    'name': 'unemployment',
                    'score': 0.0,
                    'value': None,
                    'last_updated': last_updated,
                    'interpretation': 'Current unemployment rate is NaN',
                    'data_source': 'FRED: UNRATE'
                }
            
            # Score based on Sahm indicator thresholds (0-5 points scale)
            if sahm_indicator < 0 or current <= 4.0:
                score = 0.0
                interpretation = 'Unemployment flat or falling - strong labor market'
            elif 0.5 <= sahm_indicator < 1.0:
                score = 2.5
                interpretation = f'Sahm rule early warning - indicator at {sahm_indicator:.2f}pp (0.5-0.9pp range)'
            elif sahm_indicator >= 1.0:
                score = 5.0
                interpretation = f'Sahm rule TRIGGERED - indicator at {sahm_indicator:.2f}pp (≥1.0pp) - recession signal'
            else:  # 0 < sahm_indicator < 0.5
                # Linear interpolation between 0 and 2.5 points
                score = sahm_indicator * 5
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
            import traceback
            traceback.print_exc()
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
        Category 1.3: GDP vs Stall Speed (0-5 points) - reduced from 10 points

        Scoring (reduced weighting):
        0 points: >2.5% YoY growth (strong expansion)
        2.5 points: 1.5-2.5% growth (near stall speed)
        5 points: <1.5% or 2+ negative quarters (recession imminent)
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
            
            # Score based on growth rate and weakness (0-5 points scale)
            if avg_growth_4q > 2.5:
                score = 0.0
                interpretation = f'Strong growth above trend ({avg_growth_4q:.1f}% YoY)'
            elif 1.5 <= avg_growth_4q <= 2.5:
                score = 2.5
                interpretation = f'Growth slowing but not stalled ({avg_growth_4q:.1f}% YoY)'
            elif avg_growth_4q < 1.5 or negative_quarters >= 2:
                score = 5.0
                if negative_quarters >= 2:
                    interpretation = f'Below stall speed ({avg_growth_4q:.1f}% YoY) with {negative_quarters} negative quarters - recession risk'
                else:
                    interpretation = f'Below stall speed ({avg_growth_4q:.1f}% YoY) - recession risk'
            else:
                # Linear interpolation for edge cases
                score = min(5.0, (2.5 - avg_growth_4q) / 0.2)
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
    
    def _score_u6_deterioration(self) -> Dict[str, Any]:
        """
        Category 1.4: U-6 Underemployment Deterioration (0-4 points)

        Tracks change in U-6 from its recent low. Rising U-6 while U-3
        stays flat signals hidden labor market slack building.

        Scoring:
        0 points: U-6 falling or stable (healthy)
        1.5 points: U-6 up 0.5-1.0pp from recent low
        4 points: U-6 up >1.0pp from recent low (significant slack)
        """
        try:
            # Fetch 24 months for proper baseline
            u6 = self.fred.fetch_series('U6RATE', start_date='2023-01-01')

            if len(u6) < 12:
                return {
                    'name': 'u6_underemployment',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data (need 12+ months)',
                    'data_source': 'FRED: U6RATE'
                }

            # Find trough in last 18 months
            trough_18m = u6.iloc[-18:].min() if len(u6) >= 18 else u6.min()
            current_u6 = u6.iloc[-1]

            # Calculate deterioration
            u6_change = current_u6 - trough_18m

            # Score based on deterioration magnitude
            if u6_change <= 0:
                score = 0.0
                interpretation = 'Underemployment improving or stable'
            elif 0.5 <= u6_change < 1.0:
                score = 1.5
                interpretation = f'Moderate underemployment increase (+{u6_change:.1f}pp)'
            elif u6_change >= 1.0:
                score = 4.0
                interpretation = f'Significant underemployment increase (+{u6_change:.1f}pp) - hidden slack building'
            else:  # 0 < u6_change < 0.5
                score = u6_change * 3.2  # Linear interpolation (0.5pp = 1.6pts, scaled to 4 max)
                interpretation = f'Minor underemployment increase (+{u6_change:.1f}pp)'

            return {
                'name': 'u6_underemployment',
                'score': round(score, 1),
                'value': round(current_u6, 2),
                'change_from_trough': round(u6_change, 2),
                'trough_18m': round(trough_18m, 2),
                'last_updated': self._get_latest_timestamp(u6),
                'interpretation': interpretation,
                'data_source': 'FRED: U6RATE'
            }

        except Exception as e:
            print(f"Warning: Error scoring U-6 underemployment: {e}")
            return {
                'name': 'u6_underemployment',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'FRED: U6RATE'
            }

    def _score_labor_market_softness(self) -> Dict[str, Any]:
        """
        Category 1.5: Labor Market Softness Index (0-3 points)

        Combines:
        - Job openings decline from peak (0-1.5 pts)
        - Quit rate decline from peak (0-1.5 pts)

        Scoring:
        0 points: Openings & quits strong (expansion)
        1-2 points: Moderate cooling (late-cycle)
        3 points: Sharp deterioration (pre-recession)
        """
        try:
            # Fetch job openings (JOLTS, monthly)
            jolts = self.fred.fetch_series('JTSJOL', start_date='2022-01-01')
            quits = self.fred.fetch_series('JTSQUR', start_date='2022-01-01')

            if len(jolts) < 12 or len(quits) < 12:
                return {
                    'name': 'labor_market_softness',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'FRED: JTSJOL, JTSQUR'
                }

            # Job Openings Component (0-1.5 points)
            peak_openings = jolts.iloc[-24:].max() if len(jolts) >= 24 else jolts.max()
            current_openings = jolts.iloc[-1]
            openings_decline_pct = ((peak_openings - current_openings) / peak_openings) * 100

            if openings_decline_pct < 10:
                openings_score = 0.0
            elif openings_decline_pct < 20:
                openings_score = 0.5
            elif openings_decline_pct < 30:
                openings_score = 1.0
            else:  # >30% decline
                openings_score = 1.5

            # Quit Rate Component (0-1.5 points)
            peak_quits = quits.iloc[-24:].max() if len(quits) >= 24 else quits.max()
            current_quits = quits.iloc[-1]
            quits_decline_pct = ((peak_quits - current_quits) / peak_quits) * 100

            if quits_decline_pct < 10:
                quits_score = 0.0
            elif quits_decline_pct < 20:
                quits_score = 0.5
            elif quits_decline_pct < 30:
                quits_score = 1.0
            else:  # >30% decline
                quits_score = 1.5

            total_score = openings_score + quits_score

            # Interpretation
            if total_score <= 0.5:
                interpretation = 'Labor demand strong - healthy hiring environment'
            elif total_score <= 2:
                interpretation = f'Labor demand cooling - openings down {openings_decline_pct:.0f}%, quits down {quits_decline_pct:.0f}%'
            else:
                interpretation = f'Labor demand weakening sharply - pre-recession pattern (openings -{openings_decline_pct:.0f}%, quits -{quits_decline_pct:.0f}%)'

            return {
                'name': 'labor_market_softness',
                'score': round(total_score, 1),
                'job_openings_millions': round(current_openings / 1000, 1),
                'openings_decline_pct': round(openings_decline_pct, 1),
                'quit_rate_pct': round(current_quits, 2),
                'quits_decline_pct': round(quits_decline_pct, 1),
                'last_updated': self._get_latest_timestamp(jolts),
                'interpretation': interpretation,
                'data_source': 'FRED: JTSJOL, JTSQUR'
            }

        except Exception as e:
            print(f"Warning: Error scoring labor market softness: {e}")
            return {
                'name': 'labor_market_softness',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'FRED: JTSJOL, JTSQUR'
            }

    def _score_high_income_sector_stress(self) -> Dict[str, Any]:
        """
        Category 1.6: High-Income Sector Stress (0-3 points)

        Tracks employment changes in:
        - Information sector (USINFO) - proxy for tech sector
        - Financial activities sector (USFIRE) - proxy for finance sector

        Uses 3-month employment change to smooth volatility and capture trends.
        Fully automated via FRED API - no manual data required.

        Scoring:
        0 points: Both sectors adding jobs
        1-2 points: One sector declining moderately
        3 points: Both sectors declining significantly (white-collar recession signal)
        """
        try:
            # Fetch sector employment data (need at least 6 months for 3-month change)
            info = self.fred.fetch_series('USINFO', start_date='2023-01-01')  # Information (tech proxy)
            finance = self.fred.fetch_series('USFIRE', start_date='2023-01-01')  # Financial activities

            if len(info) < 6 or len(finance) < 6:
                return {
                    'name': 'high_income_stress',
                    'score': 0.0,
                    'error': 'Insufficient data for 3-month change calculation',
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'FRED: USINFO, USFIRE'
                }

            # Calculate 3-month change (to smooth volatility)
            # Values are in thousands of jobs
            info_change_3m = info.iloc[-1] - info.iloc[-4]  # Thousands of jobs
            finance_change_3m = finance.iloc[-1] - finance.iloc[-4]

            # Information sector component (0-1.5 pts)
            if info_change_3m < -50:  # Losing >50k jobs in 3 months
                info_score = 1.5
            elif info_change_3m < -20:  # Losing 20-50k jobs
                info_score = 1.0
            elif info_change_3m < 0:  # Losing <20k jobs
                info_score = 0.3
            else:  # Adding jobs or flat
                info_score = 0.0

            # Finance sector component (0-1.5 pts)
            if finance_change_3m < -30:  # Losing >30k jobs in 3 months
                finance_score = 1.5
            elif finance_change_3m < -10:  # Losing 10-30k jobs
                finance_score = 1.0
            elif finance_change_3m < 0:  # Losing <10k jobs
                finance_score = 0.3
            else:  # Adding jobs or flat
                finance_score = 0.0

            total_score = min(3.0, info_score + finance_score)  # Cap at 3.0

            # Interpretation
            if total_score == 0:
                interpretation = 'High-income sectors adding jobs - no stress'
            elif total_score <= 1.5:
                interpretation = f'Moderate stress in high-income sectors (info: {info_change_3m/1000:.0f}k, finance: {finance_change_3m/1000:.0f}k 3-month change)'
            else:
                interpretation = f'Severe stress in high-income sectors - white-collar recession signal (info: {info_change_3m/1000:.0f}k, finance: {finance_change_3m/1000:.0f}k)'

            return {
                'name': 'high_income_stress',
                'score': round(total_score, 1),
                'info_sector_change_3m': int(info_change_3m),
                'finance_sector_change_3m': int(finance_change_3m),
                'info_sector_current': int(info.iloc[-1]),
                'finance_sector_current': int(finance.iloc[-1]),
                'last_updated': self._get_latest_timestamp(info),
                'interpretation': interpretation,
                'data_source': 'FRED: USINFO, USFIRE'
            }

        except Exception as e:
            print(f"Warning: Error scoring high-income sector stress: {e}")
            return {
                'name': 'high_income_stress',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'FRED: USINFO, USFIRE'
            }

    def _determine_risk_level(self, score: float) -> str:
        """Map score to risk level"""
        if score < 8:
            return "LOW"
        elif score < 16:
            return "MODERATE"
        elif score < 23:
            return "ELEVATED"
        else:
            return "SEVERE"

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
            description='Enhanced macro/cycle assessment with traditional recession indicators (unemployment, yield curve, GDP) plus leading labor market quality indicators (U-6 underemployment, job openings/quits, high-income sector employment trends).',
            update_frequency='Mixed: Monthly (Unemployment, U-6, Sector Employment), Monthly+1 (JOLTS), Daily (Yield Curve), Quarterly (GDP)',
            data_sources=[
                'FRED: UNRATE (Unemployment)',
                'FRED: T10Y2Y (Yield Curve)',
                'FRED: GDPC1 (GDP)',
                'FRED: U6RATE (U-6 Underemployment)',
                'FRED: JTSJOL (Job Openings)',
                'FRED: JTSQUR (Quit Rate)',
                'FRED: USINFO (Information Sector Employment)',
                'FRED: USFIRE (Financial Sector Employment)'
            ],
            next_update=f"{first_friday.strftime('%Y-%m-%d')} (Unemployment, U-6, Sector Employment)"
        )


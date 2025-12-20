"""
Category 2: Valuation (0-25 points)
Assesses whether stocks are expensive relative to fundamentals
"""

from datetime import datetime
from typing import Dict, Any, Optional
from .base_category import BaseCategory, ComponentScore, CategoryMetadata


class ValuationCategory(BaseCategory):
    """Category 2: Valuation Risk Assessment"""
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate valuation category score"""
        pe_score = self._score_forward_pe()
        buffett_score = self._score_buffett_indicator()
        equity_yield_score = self._score_equity_yield_vs_tbill()
        
        # Scale to max 25 points
        raw_total = pe_score['score'] + buffett_score['score'] + equity_yield_score['score']
        total_score = min(25.0, raw_total * 25 / 30)
        
        return {
            'score': round(total_score, 1),
            'max_points': 25.0,
            'components': {
                'forward_pe': pe_score,
                'buffett_indicator': buffett_score,
                'equity_yield': equity_yield_score,
            },
            'metadata': self.get_metadata(),
        }
    
    def _score_forward_pe(self) -> Dict[str, Any]:
        """
        Category 2.1: Forward P/E vs Historical (0-10 points)
        Reference Guide Spec:
        - ≤16x: 0 points (historical median)
        - 16-19.5x: Linear interpolation 0-5 points (1 SD above)
        - 19.5-22x: Linear interpolation 5-10 points (extreme)
        - >22x: 10 points (dot-com/2021 levels)
        """
        try:
            # Try to get P/E (with historical estimate fallback)
            forward_pe = self.market_data.get_forward_pe('SPY', use_historical_estimate=True)
            
            if forward_pe is None:
                print(f"  ℹ P/E not available, using default moderate risk score")
                return {
                    'name': 'forward_pe',
                    'score': 5.0,
                    'value': None,
                    'last_updated': datetime.now().isoformat(),
                    'interpretation': 'Data unavailable - using default moderate risk score',
                    'data_source': 'Yahoo Finance: ^GSPC'
                }
            
            # Define thresholds per reference guide
            historical_median = 16.0
            one_sd_above = 19.5
            extreme_level = 22.0
            
            # Calculate score with linear interpolation
            if forward_pe <= historical_median:
                score = 0.0
                interpretation = 'At or below historical median - fair value'
            elif forward_pe <= one_sd_above:
                # Linear interpolation 0-5 between 16 and 19.5
                score = (forward_pe - historical_median) / (one_sd_above - historical_median) * 5.0
                interpretation = f'Moderately expensive ({score:.1f}/5 in range)'
            elif forward_pe <= extreme_level:
                # Linear interpolation 5-10 between 19.5 and 22
                score = 5.0 + (forward_pe - one_sd_above) / (extreme_level - one_sd_above) * 5.0
                interpretation = f'Very expensive ({score:.1f}/10 - approaching bubble)'
            else:
                score = 10.0
                interpretation = 'Dot-com/2021 bubble levels - extreme valuation'
            
            return {
                'name': 'forward_pe',
                'score': round(score, 1),
                'value': round(forward_pe, 2),
                'last_updated': datetime.now().isoformat(),
                'interpretation': interpretation,
                'data_source': 'Yahoo Finance: ^GSPC'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring forward P/E: {e}")
            return {
                'name': 'forward_pe',
                'score': 5.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)} - using default score',
                'data_source': 'Yahoo Finance: ^GSPC'
            }
    
    def _score_buffett_indicator(self) -> Dict[str, Any]:
        """
        Category 2.2: Buffett Indicator (0-10 points)
        Reference Guide Spec:
        - <100%: 0 points (normal range)
        - 100-140%: Linear interpolation 0-5 points
        - >140%: Linear interpolation 5-10 points (capped at 10)
        """
        try:
            # Market cap / GDP ratio
            # DDDM01USA156NWDB = Market capitalization of listed domestic companies (% of GDP)
            buffett_ratio = self.fred.fetch_series('DDDM01USA156NWDB', start_date='2020-01-01')
            
            if len(buffett_ratio) == 0:
                return {
                    'name': 'buffett_indicator',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'No data available',
                    'data_source': 'FRED: DDDM01USA156NWDB'
                }
            
            # Get latest value (already in percentage)
            ratio = buffett_ratio.iloc[-1]
            last_updated = self._get_latest_timestamp(buffett_ratio)
            
            # Calculate score with linear interpolation per reference guide
            if ratio < 100:
                score = 0.0
                interpretation = 'Normal range - fair value or better'
            elif ratio <= 140:
                # Linear interpolation 0-5 between 100 and 140
                score = (ratio - 100) / 40 * 5.0
                interpretation = f'High but below prior peaks ({score:.1f}/5 - very expensive)'
            else:
                # Linear interpolation 5-10 above 140, capped at 10
                score = min(10.0, 5.0 + (ratio - 140) / 40 * 5.0)
                interpretation = f'At/above dot-com & 2007 highs ({score:.1f}/10 - extreme bubble territory)'
            
            return {
                'name': 'buffett_indicator',
                'score': round(score, 1),
                'value': round(ratio, 2),
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'FRED: DDDM01USA156NWDB'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring Buffett Indicator: {e}")
            return {
                'name': 'buffett_indicator',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'FRED: DDDM01USA156NWDB'
            }
    
    def _score_equity_yield_vs_tbill(self) -> Dict[str, Any]:
        """
        Category 2.3: Equity Yield vs T-Bills (0-10 points)
        Reference Guide Spec:
        - >2.0pp spread: 0 points (adequate premium)
        - -0.5 to 2.0pp: Linear interpolation 0-5 points
        - <-0.5pp: Linear interpolation 5-10 points (inverted premium)
        """
        try:
            # Get forward P/E to calculate earnings yield (with historical estimate fallback)
            forward_pe = self.market_data.get_forward_pe('SPY', use_historical_estimate=True)
            if forward_pe is None or forward_pe <= 0:
                print(f"  ℹ Equity yield not available, using default score")
                return {
                    'name': 'equity_yield',
                    'score': 5.0,
                    'value': None,
                    'last_updated': datetime.now().isoformat(),
                    'interpretation': 'Data unavailable - using default moderate risk score',
                    'data_source': 'Yahoo Finance + FRED: DTB3, DTB6'
                }
            
            earnings_yield = (1.0 / forward_pe) * 100  # Percentage
            
            # Get 3-month and 6-month T-bill rates and average them per reference guide
            tbill_3m = self.fred.get_latest_value('DTB3')
            tbill_6m = self.fred.get_latest_value('DTB6')
            
            if tbill_3m is None or tbill_6m is None:
                # Fallback to just 3M if 6M unavailable
                if tbill_3m is not None:
                    tbill_avg = tbill_3m
                    print(f"  ℹ Using only DTB3 (DTB6 unavailable)")
                else:
                    return {
                        'name': 'equity_yield',
                        'score': 0.0,
                        'value': None,
                        'last_updated': None,
                        'interpretation': 'T-bill data unavailable',
                        'data_source': 'FRED: DTB3, DTB6'
                    }
            else:
                # Average 3M and 6M per reference guide specification
                tbill_avg = (tbill_3m + tbill_6m) / 2.0
            
            spread = earnings_yield - tbill_avg
            
            # Calculate score with linear interpolation per reference guide
            if spread > 2.0:
                score = 0.0
                interpretation = 'Adequate equity risk premium (>2pp)'
            elif spread >= -0.5:
                # Linear interpolation 0-5 between 2.0 and -0.5
                score = (2.0 - spread) / 2.5 * 5.0
                interpretation = f'Shrinking equity premium ({score:.1f}/5 - minimal compensation for risk)'
            else:
                # Linear interpolation 5-10 below -0.5, capped at 10
                score = min(10.0, 5.0 + (-0.5 - spread) / 2.0 * 5.0)
                interpretation = f'Inverted risk premium ({score:.1f}/10 - no compensation for equity risk)'
            
            return {
                'name': 'equity_yield',
                'score': round(score, 1),
                'value': round(spread, 2),
                'last_updated': datetime.now().isoformat(),
                'interpretation': interpretation,
                'data_source': 'Yahoo Finance + FRED: DTB3, DTB6'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring equity yield: {e}")
            return {
                'name': 'equity_yield',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'Yahoo Finance + FRED: DTB3, DTB6'
            }
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        return CategoryMetadata(
            name='Valuation',
            max_points=25.0,
            description='Assesses whether stocks are expensive relative to fundamentals through forward P/E ratios, the Buffett Indicator (market cap/GDP), and equity yield vs risk-free rates.',
            update_frequency='Daily (P/E, Equity Yield), Quarterly (Buffett Indicator)',
            data_sources=[
                'Yahoo Finance: SPY (P/E ratio fundamental data)',
                'FRED: DDDM01USA156NWDB (Buffett Indicator)',
                'FRED: DTB3 (3-month T-bill rate)',
                'FRED: DTB6 (6-month T-bill rate)'
            ],
            next_update='Daily (after market close)'
        )


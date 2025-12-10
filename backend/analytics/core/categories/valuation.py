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
        0 points: ≤ Historical median (~16x)
        5 points: 1 SD above (~19-20x)
        10 points: Dot-com/2021 levels (22x+)
        """
        try:
            # Try to get P/E (with historical estimate fallback)
            forward_pe = self.yfinance.get_forward_pe('SPY', use_historical_estimate=True)
            
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
            
            if forward_pe <= 16:
                score = 0.0
                interpretation = 'At or below historical median - fair value'
            elif forward_pe <= 20:
                score = 5.0
                interpretation = '1 SD above median - expensive'
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
        0 points: Normal range (<100%)
        5 points: High but below prior peaks (100-140%)
        10 points: At/above dot-com & 2007 highs (>140%)
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
            
            if ratio < 100:
                score = 0.0
                interpretation = 'Normal range - fair value or better'
            elif ratio < 140:
                score = 5.0
                interpretation = 'High but below prior peaks - very expensive'
            else:
                score = 10.0
                interpretation = 'At/above dot-com & 2007 highs - extreme bubble territory'
            
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
        0 points: Earnings yield >> T-bill yield
        5 points: Roughly equal
        10 points: Equity yield < T-bill yield
        """
        try:
            # Get forward P/E to calculate earnings yield (with historical estimate fallback)
            forward_pe = self.yfinance.get_forward_pe('SPY', use_historical_estimate=True)
            if forward_pe is None or forward_pe <= 0:
                print(f"  ℹ Equity yield not available, using default score")
                return {
                    'name': 'equity_yield',
                    'score': 5.0,
                    'value': None,
                    'last_updated': datetime.now().isoformat(),
                    'interpretation': 'Data unavailable - using default moderate risk score',
                    'data_source': 'Yahoo Finance + FRED: DTB3'
                }
            
            earnings_yield = (1.0 / forward_pe) * 100  # Percentage
            
            # Get 3-month T-bill rate
            tbill_3m = self.fred.get_latest_value('DTB3')
            if tbill_3m is None:
                return {
                    'name': 'equity_yield',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'T-bill data unavailable',
                    'data_source': 'FRED: DTB3'
                }
            
            spread = earnings_yield - tbill_3m
            
            if spread > 2.0:
                score = 0.0
                interpretation = 'Adequate equity risk premium (>2pp)'
            elif spread > 0:
                score = 5.0
                interpretation = 'Shrinking equity premium - minimal compensation for risk'
            else:
                score = 10.0
                interpretation = 'Inverted risk premium - no compensation for equity risk'
            
            return {
                'name': 'equity_yield',
                'score': round(score, 1),
                'value': round(spread, 2),
                'last_updated': datetime.now().isoformat(),
                'interpretation': interpretation,
                'data_source': 'Yahoo Finance + FRED: DTB3'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring equity yield: {e}")
            return {
                'name': 'equity_yield',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'Yahoo Finance + FRED: DTB3'
            }
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        return CategoryMetadata(
            name='Valuation',
            max_points=25.0,
            description='Assesses whether stocks are expensive relative to fundamentals through forward P/E ratios, the Buffett Indicator (market cap/GDP), and equity yield vs risk-free rates.',
            update_frequency='Daily (P/E, Equity Yield), Quarterly (Buffett Indicator)',
            data_sources=['Yahoo Finance: ^GSPC', 'FRED: DDDM01USA156NWDB', 'FRED: DTB3'],
            next_update='Daily (after market close)'
        )


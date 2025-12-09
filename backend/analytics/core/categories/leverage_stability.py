"""
Category 3: Leverage & Financial Stability (0-25 points)
Identifies hidden fragilities and systemic risks in the financial system
"""

from datetime import datetime
from typing import Dict, Any, Optional
from .base_category import BaseCategory, ComponentScore, CategoryMetadata


class LeverageStabilityCategory(BaseCategory):
    """Category 3: Leverage & Financial Stability Risk Assessment"""
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate leverage/stability category score"""
        hedge_fund_score = self._score_hedge_fund_leverage()
        corp_credit_score = self._score_corporate_credit()
        cre_score = self._score_cre_stress()
        
        # Scale to max 25 points
        raw_total = hedge_fund_score['score'] + corp_credit_score['score'] + cre_score['score']
        total_score = min(25.0, raw_total * 25 / 30)
        
        return {
            'score': round(total_score, 1),
            'max_points': 25.0,
            'components': {
                'hedge_fund_leverage': hedge_fund_score,
                'corporate_credit': corp_credit_score,
                'cre_stress': cre_score,
            },
            'metadata': self.get_metadata(),
        }
    
    def _score_hedge_fund_leverage(self) -> Dict[str, Any]:
        """
        Category 3.1: Hedge Fund Leverage (0-10 points)
        Manual input from Fed Financial Stability Report
        """
        leverage_value = self.manual_inputs.get('hedge_fund_leverage', 0)
        leverage_as_of = self.manual_inputs.get('hedge_fund_leverage_as_of', None)
        
        return {
            'name': 'hedge_fund_leverage',
            'score': round(float(leverage_value), 1),
            'value': float(leverage_value),
            'last_updated': leverage_as_of,
            'interpretation': f'Hedge fund leverage score: {leverage_value}/10 (manual input from Fed FSR)',
            'data_source': 'Manual: Fed Financial Stability Report (Semi-annual)',
            'is_manual': True,
            'next_update': '2026-05-01 (Next Fed FSR)'
        }
    
    def _score_corporate_credit(self) -> Dict[str, Any]:
        """
        Category 3.2: Corporate Credit Health (0-10 points)
        0 points: Tight spreads, strong coverage
        5 points: Mild deterioration
        10 points: Widespread distress
        """
        try:
            # Fetch HY spread
            hy_spread = self.fred.fetch_series('BAMLH0A0HYM2', start_date='2020-01-01')
            
            if len(hy_spread) == 0:
                return {
                    'name': 'corporate_credit',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'No data available',
                    'data_source': 'FRED: BAMLH0A0HYM2'
                }
            
            current_spread = hy_spread.iloc[-1]
            last_updated = self._get_latest_timestamp(hy_spread)
            
            # Normalize: <400bps = 0, 400-600 = 5, >600 = 10
            if current_spread < 400:
                score = 0.0
                interpretation = 'Tight spreads - healthy credit conditions'
            elif current_spread < 600:
                score = 5.0
                interpretation = 'Elevated spreads - mild deterioration'
            else:
                score = 10.0
                interpretation = 'Wide spreads - widespread distress'
            
            return {
                'name': 'corporate_credit',
                'score': round(score, 1),
                'value': round(current_spread, 2),
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'FRED: BAMLH0A0HYM2'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring corporate credit: {e}")
            return {
                'name': 'corporate_credit',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'FRED: BAMLH0A0HYM2'
            }
    
    def _score_cre_stress(self) -> Dict[str, Any]:
        """
        Category 3.3: CRE / Regional Bank Stress (0-10 points)
        Manual input for now (would need FDIC data)
        """
        delinquency_rate = self.manual_inputs.get('cre_delinquency_rate', 0)
        cre_as_of = self.manual_inputs.get('cre_delinquency_as_of', None)
        
        if delinquency_rate < 2.0:
            score = 0.0
            interpretation = 'Low delinquency - healthy CRE market'
        elif delinquency_rate < 5.0:
            score = 5.0
            interpretation = 'Moderate delinquency - concerning but manageable'
        else:
            score = 10.0
            interpretation = 'High delinquency - systemic risk'
        
        return {
            'name': 'cre_stress',
            'score': round(score, 1),
            'value': round(float(delinquency_rate), 2),
            'last_updated': cre_as_of,
            'interpretation': interpretation,
            'data_source': 'Manual: FDIC Quarterly Banking Profile',
            'is_manual': True,
            'next_update': '2026-02-15 (Next FDIC QBP)'
        }
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        return CategoryMetadata(
            name='Leverage & Stability',
            max_points=25.0,
            description='Identifies hidden fragilities and systemic risks through hedge fund leverage, corporate credit spreads, and commercial real estate stress.',
            update_frequency='Daily (Credit Spreads), Semi-annual (Hedge Fund Leverage), Quarterly (CRE)',
            data_sources=['FRED: BAMLH0A0HYM2', 'Manual: Fed FSR', 'Manual: FDIC QBP'],
            next_update='2026-02-15 (FDIC Quarterly Banking Profile)'
        )


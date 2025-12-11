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
        """
        Calculate leverage/stability category score
        Sum all three indicators and cap at 25 points
        """
        hedge_fund_score = self._score_hedge_fund_leverage()
        corp_credit_score = self._score_corporate_credit()
        cre_score = self._score_cre_stress()
        
        # Sum all three components (each 0-10) and cap at 25
        raw_total = hedge_fund_score['score'] + corp_credit_score['score'] + cre_score['score']
        total_score = min(25.0, raw_total)
        
        return {
            'score': round(total_score, 1),
            'max_points': 25.0,
            'raw_total': round(raw_total, 1),
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
        
        Scoring:
        - <60th percentile, no concern: 0 points
        - 60-75th: 1-4 points
        - 75-90th: 5 points
        - >90th OR regulator warnings: 8-10 points
        """
        leverage_percentile = self.manual_inputs.get('hedge_fund_leverage_percentile', 50)
        basis_concern = self.manual_inputs.get('hedge_fund_basis_trade_concern', False)
        leverage_as_of = self.manual_inputs.get('hedge_fund_leverage_as_of', None)
        basis_trade_notional = self.manual_inputs.get('hedge_fund_basis_trade_notional', None)
        
        # Determine score based on percentile and concerns
        if leverage_percentile < 60 and not basis_concern:
            score = 0.0
            interpretation = 'Low systemic risk - leverage below 60th percentile'
        elif 60 <= leverage_percentile < 75:
            score = 1 + ((leverage_percentile - 60) / 15) * 3  # Linear 1-4
            interpretation = 'Moderately elevated leverage'
        elif 75 <= leverage_percentile < 90:
            score = 4 + ((leverage_percentile - 75) / 15) * 4  # Linear 4-8
            interpretation = 'Elevated but stable leverage'
        else:  # >= 90 or basis_concern flagged
            score = 8 + min(2, (leverage_percentile - 90) / 5)  # 8-10
            interpretation = 'Record leverage - maximum systemic risk'
        
        # If basis trade concern is flagged, ensure minimum score of 8
        if basis_concern and score < 8:
            score = 8.0
            interpretation = 'Basis trade concentration risk flagged by regulators'
        
        result = {
            'name': 'hedge_fund_leverage',
            'score': round(float(score), 1),
            'value': float(leverage_percentile),
            'last_updated': leverage_as_of,
            'interpretation': interpretation,
            'data_source': 'Manual: Fed Financial Stability Report (Semi-annual)',
            'is_manual': True,
            'next_update': '2026-05-01 (Next Fed FSR)'
        }
        
        if basis_trade_notional is not None:
            result['basis_trade_notional_billions'] = basis_trade_notional
        
        return result
    
    def _score_corporate_credit(self) -> Dict[str, Any]:
        """
        Category 3.2: Corporate Credit Health (0-10 points)
        Uses HY spreads with percentile-based scoring
        
        Scoring thresholds (in basis points):
        - <300 or <50th percentile: 0
        - 300-450 or 50-75th: 1-5
        - 450-600 or 75-85th: 5-8
        - 600-800 or 85-90th: 8-9
        - >800 or >90th: 9-10
        """
        try:
            # Fetch HY spread (5 years for percentile calculation)
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
            
            # Calculate percentiles for context
            median_spread = hy_spread.median()
            pct_75 = hy_spread.quantile(0.75)
            pct_90 = hy_spread.quantile(0.90)
            
            # Score based on absolute thresholds and percentile ranking
            if current_spread < 300:
                score = 0.0
                interpretation = 'Very tight spreads - healthy credit conditions'
            elif current_spread < 450:
                # Linear interpolation 0-5
                score = (current_spread - 300) / 150 * 5
                interpretation = 'Moderately elevated spreads'
            elif current_spread < 600:
                # Linear interpolation 5-8
                score = 5 + (current_spread - 450) / 150 * 3
                interpretation = 'Widening spreads - some credit stress'
            elif current_spread < 800:
                # Linear interpolation 8-9
                score = 8 + (current_spread - 600) / 200 * 1
                interpretation = 'Significant stress - elevated default risk'
            else:  # >= 800
                score = 9 + min(1, (current_spread - 800) / 400)
                interpretation = 'Crisis levels - widespread distress'
            
            return {
                'name': 'corporate_credit',
                'score': round(score, 1),
                'value': round(current_spread, 2),
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'FRED: BAMLH0A0HYM2',
                'median_5y': round(median_spread, 2),
                'percentile_75': round(pct_75, 2),
                'percentile_90': round(pct_90, 2)
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
        Two-part scoring:
        - 50% from CRE delinquency (manual, FDIC)
        - 50% from Regional Bank stress (automated, KRE ETF)
        
        Scoring thresholds:
        - <3% delinquency AND drawdown > -10%: 0 points
        - 3-5% OR -10% to -15%: 1-4
        - 5-6% OR -15% to -20%: 5
        - 6-8% OR -20% to -30%: 6-9
        - >8% OR <-30%: 10 points
        """
        # PART A: CRE Delinquency (Manual)
        delinquency_rate = self.manual_inputs.get('cre_delinquency_rate', 0)
        cre_as_of = self.manual_inputs.get('cre_delinquency_as_of', None)
        office_vacancy = self.manual_inputs.get('cre_office_vacancy', None)
        
        # Score delinquency component
        if delinquency_rate < 3.0:
            delinquency_score = 0.0
            delinq_interp = 'Low delinquency - healthy CRE'
        elif delinquency_rate < 5.0:
            delinquency_score = 1 + ((delinquency_rate - 3.0) / 2.0) * 3  # Linear 1-4
            delinq_interp = 'Early deterioration'
        elif delinquency_rate < 6.0:
            delinquency_score = 4 + ((delinquency_rate - 5.0) / 1.0) * 1  # Linear 4-5
            delinq_interp = 'Concerning but manageable'
        elif delinquency_rate < 8.0:
            delinquency_score = 5 + ((delinquency_rate - 6.0) / 2.0) * 4  # Linear 5-9
            delinq_interp = 'Significant stress'
        else:  # >= 8.0
            delinquency_score = 9 + min(1, (delinquency_rate - 8.0) / 2.0)
            delinq_interp = 'Crisis levels - systemic risk'
        
        # PART B: Regional Bank Stress (Automated - KRE ETF)
        bank_score = 0.0
        kre_data = {}
        bank_interp = 'No data'
        
        try:
            if self.yfinance:
                kre = self.yfinance.get_ticker('KRE')
                hist = kre.history(period='1y')
                
                if len(hist) > 0:
                    current_price = hist['Close'].iloc[-1]
                    high_52w = hist['High'].max()
                    drawdown = ((current_price - high_52w) / high_52w) * 100
                    
                    # Score based on drawdown
                    if drawdown > -10:
                        bank_score = 0.0
                        bank_interp = 'Regional banks healthy'
                    elif drawdown > -15:
                        bank_score = 1 + ((-10 - drawdown) / 5) * 3  # Linear 1-4
                        bank_interp = 'Moderate bank stress'
                    elif drawdown > -20:
                        bank_score = 4 + ((-15 - drawdown) / 5) * 1  # Linear 4-5
                        bank_interp = 'Concerning bank weakness'
                    elif drawdown > -30:
                        bank_score = 5 + ((-20 - drawdown) / 10) * 4  # Linear 5-9
                        bank_interp = 'Significant bank stress'
                    else:  # <= -30
                        bank_score = 9 + min(1, (-30 - drawdown) / 20)
                        bank_interp = 'Bank crisis levels'
                    
                    kre_data = {
                        'kre_current_price': round(current_price, 2),
                        'kre_52w_high': round(high_52w, 2),
                        'kre_drawdown_pct': round(drawdown, 2)
                    }
        except Exception as e:
            print(f"Warning: Error fetching KRE data: {e}")
            bank_score = 0.0
            bank_interp = f'Error fetching bank data: {str(e)}'
        
        # PART C: Combined Score (50/50 weighting)
        combined_score = (delinquency_score * 0.5) + (bank_score * 0.5)
        
        # Overall interpretation
        if combined_score < 3:
            overall_interp = f'Healthy CRE market. {delinq_interp}. {bank_interp}.'
        elif combined_score < 6:
            overall_interp = f'Rising concerns. {delinq_interp}. {bank_interp}.'
        else:
            overall_interp = f'Systemic stress. {delinq_interp}. {bank_interp}.'
        
        result = {
            'name': 'cre_stress',
            'score': round(combined_score, 1),
            'value': round(float(delinquency_rate), 2),
            'last_updated': cre_as_of,
            'interpretation': overall_interp,
            'data_source': 'Manual: FDIC QBP (Delinquency) + Yahoo Finance: KRE (Bank Stress)',
            'is_manual': True,
            'next_update': '2026-02-15 (Next FDIC QBP)',
            'delinquency_score': round(delinquency_score, 1),
            'bank_stress_score': round(bank_score, 1),
        }
        
        # Add optional data if available
        if office_vacancy is not None:
            result['office_vacancy_pct'] = round(float(office_vacancy), 2)
        
        result.update(kre_data)
        
        return result
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        return CategoryMetadata(
            name='Leverage & Stability',
            max_points=25.0,
            description='Identifies hidden fragilities and systemic risks through hedge fund leverage, corporate credit spreads, and commercial real estate stress.',
            update_frequency='Daily (Credit Spreads, Regional Banks), Semi-annual (Hedge Fund Leverage), Quarterly (CRE Delinquency)',
            data_sources=['FRED: BAMLH0A0HYM2', 'Yahoo Finance: KRE', 'Manual: Fed FSR', 'Manual: FDIC QBP'],
            next_update='2026-02-15 (FDIC Quarterly Banking Profile)'
        )


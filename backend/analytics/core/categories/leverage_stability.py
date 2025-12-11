"""
Category 3: Leverage & Financial Stability (0-25 points)
Identifies hidden fragilities and systemic risks in the financial system

Enhanced with:
- Hedge fund leverage with basis trade concentration tracking
- Corporate credit with interest coverage, default momentum, recovery rates
- CRE stress with 4-component scoring (delinquency, bank stress, refinancing cliff, vacancy)
- Cross-sector contagion multiplier for systemic amplification risk
"""

from datetime import datetime
from typing import Dict, Any, Optional
from .base_category import BaseCategory, ComponentScore, CategoryMetadata


class LeverageStabilityCategory(BaseCategory):
    """Category 3: Leverage & Financial Stability Risk Assessment"""
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calculate leverage/stability category score with contagion multiplier
        Sum all three indicators, apply contagion multiplier, cap at 25 points
        """
        hedge_fund_score = self._score_hedge_fund_leverage()
        corp_credit_score = self._score_corporate_credit()
        cre_score = self._score_cre_stress()
        
        # Raw total before contagion multiplier
        raw_total = hedge_fund_score['score'] + corp_credit_score['score'] + cre_score['score']
        
        # Calculate contagion multiplier (1.0 to 1.5)
        contagion_mult = self._calculate_contagion_multiplier(
            hedge_fund_score['score'],
            corp_credit_score['score'],
            cre_score['score']
        )
        
        # Apply contagion multiplier and cap at 25
        adjusted_total = raw_total * contagion_mult
        total_score = min(25.0, adjusted_total)
        
        # Generate risk narrative
        risk_narrative = self._get_risk_narrative(
            total_score, 
            hedge_fund_score, 
            corp_credit_score, 
            cre_score
        )
        
        return {
            'score': round(total_score, 1),
            'max_points': 25.0,
            'raw_total': round(raw_total, 1),
            'contagion_multiplier': round(contagion_mult, 2),
            'adjusted_total': round(adjusted_total, 1),
            'systemic_risk_level': self._assess_systemic_level(total_score),
            'risk_narrative': risk_narrative,
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
        
        Scoring (CORRECTED):
        - <60th percentile, no concern: 0 points
        - 60-75th: 1-4 points (linear)
        - 75-90th: 5.0 points (FIXED VALUE per specification)
        - >90th OR regulator warnings: 8-10 points
        
        Enhanced with:
        - Basis trade concentration tracking (notional / Treasury market size)
        - Dealer capacity constraints (SLR ratios)
        """
        leverage_percentile = self.manual_inputs.get('hedge_fund_leverage_percentile', 50)
        basis_concern = self.manual_inputs.get('hedge_fund_basis_trade_concern', False)
        leverage_as_of = self.manual_inputs.get('hedge_fund_leverage_as_of', None)
        basis_trade_notional = self.manual_inputs.get('hedge_fund_basis_trade_notional', 0)
        dealer_slr = self.manual_inputs.get('primary_dealer_slr_ratio', 7.0)
        
        # Base scoring (CORRECTED)
        if leverage_percentile < 60 and not basis_concern:
            score = 0.0
            interpretation = 'Low systemic risk - leverage below 60th percentile'
        elif 60 <= leverage_percentile < 75:
            score = 1 + ((leverage_percentile - 60) / 15) * 3  # Linear 1-4
            interpretation = 'Moderately elevated leverage'
        elif 75 <= leverage_percentile < 90:
            score = 5.0  # FIXED VALUE - per Reference Guide specification
            interpretation = 'Elevated but stable leverage'
        else:  # >= 90
            score = 8 + min(2, (leverage_percentile - 90) / 5)  # 8-10
            interpretation = 'Record leverage - maximum systemic risk'
        
        # Basis trade concentration analysis
        treasury_market_size = 27000  # ~$27T total Treasury market
        basis_concentration = 0.0
        conc_warning = None
        
        if basis_trade_notional > 0:
            basis_concentration = (basis_trade_notional / treasury_market_size) * 100
            
            if basis_concentration > 4.0:  # > 4% of Treasury market
                score = min(10.0, score + 2.0)
                conc_warning = 'EXTREME basis trade concentration - systemic Treasury market risk'
            elif basis_concentration > 3.0:
                score = min(10.0, score + 1.0)
                conc_warning = 'High basis trade concentration - Treasury market vulnerability'
            elif basis_concentration > 2.0:
                conc_warning = 'Elevated basis trade exposure - monitoring required'
        
        # If basis trade concern is manually flagged, ensure minimum score of 8
        if basis_concern and score < 8:
            score = 8.0
            interpretation = 'Basis trade concentration risk flagged by regulators'
        
        # Dealer capacity constraints
        dealer_warning = None
        if dealer_slr < 5.5:  # Approaching regulatory minimum (5.0%)
            score = min(10.0, score + 1.0)
            dealer_warning = 'Dealer capacity constrained - amplification risk elevated'
        elif dealer_slr < 6.0:
            dealer_warning = 'Dealer capacity tight - reduced intermediation capacity'
        
        result = {
            'name': 'hedge_fund_leverage',
            'score': round(float(score), 1),
            'value': float(leverage_percentile),
            'last_updated': leverage_as_of,
            'interpretation': interpretation,
            'data_source': 'Manual: Fed Financial Stability Report (Semi-annual)',
            'is_manual': True,
            'next_update': '2026-05-01 (Next Fed FSR)',
            'basis_trade_notional_billions': float(basis_trade_notional),
            'basis_concentration_pct': round(basis_concentration, 2),
            'dealer_slr_ratio': float(dealer_slr)
        }
        
        if conc_warning:
            result['concentration_warning'] = conc_warning
        if dealer_warning:
            result['dealer_warning'] = dealer_warning
        
        return result
    
    def _score_corporate_credit(self) -> Dict[str, Any]:
        """
        Category 3.2: Corporate Credit Health (0-10 points)
        
        Enhanced multi-factor scoring:
        - 50% HY spreads (market pricing)
        - 20% Interest coverage ratios (debt service capacity)
        - 20% Default rate momentum (trend analysis)
        - 10% Recovery rate adjustment (loss severity)
        
        Captures credit stress earlier than spreads alone
        """
        try:
            # Component 1: HY Spread Scoring (50% weight)
            spread_score = self._score_hy_spreads()
            
            # Component 2: Interest Coverage (20% weight)
            coverage_score = self._score_interest_coverage()
            
            # Component 3: Default Momentum (20% weight)
            default_score = self._score_default_momentum()
            
            # Component 4: Recovery Rate Adjustment (10% weight)
            recovery_penalty = self._score_recovery_rate()
            
            # Weighted combination
            combined_score = (
                spread_score['score'] * 0.50 +
                coverage_score['score'] * 0.20 +
                default_score['score'] * 0.20 +
                recovery_penalty['score'] * 0.10
            )
            
            # Overall interpretation
            if combined_score < 3:
                overall_interp = 'Healthy credit conditions'
            elif combined_score < 6:
                overall_interp = 'Moderate credit stress emerging'
            elif combined_score < 8:
                overall_interp = 'Elevated credit stress - defaults rising'
            else:
                overall_interp = 'Severe credit distress - widespread defaults'
            
            return {
                'name': 'corporate_credit',
                'score': round(combined_score, 1),
                'value': spread_score.get('value'),
                'last_updated': spread_score.get('last_updated'),
                'interpretation': overall_interp,
                'data_source': 'FRED: BAMLH0A0HYM2 + Manual: Fed FSR Corporate Metrics',
                'components': {
                    'hy_spreads': spread_score,
                    'interest_coverage': coverage_score,
                    'default_momentum': default_score,
                    'recovery_rate': recovery_penalty
                }
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
    
    def _score_hy_spreads(self) -> Dict[str, Any]:
        """Score based on high-yield credit spreads"""
        try:
            hy_spread = self.fred.fetch_series('BAMLH0A0HYM2', start_date='2020-01-01')
            
            if len(hy_spread) == 0:
                return {'score': 0.0, 'value': None, 'last_updated': None}
            
            current_spread = hy_spread.iloc[-1]
            last_updated = self._get_latest_timestamp(hy_spread)
            
            # Score based on absolute thresholds
            if current_spread < 300:
                score = 0.0
                interp = 'Very tight spreads'
            elif current_spread < 450:
                score = (current_spread - 300) / 150 * 5
                interp = 'Moderately elevated'
            elif current_spread < 600:
                score = 5 + (current_spread - 450) / 150 * 3
                interp = 'Widening - stress building'
            elif current_spread < 800:
                score = 8 + (current_spread - 600) / 200 * 1
                interp = 'Significant stress'
            else:
                score = 9 + min(1, (current_spread - 800) / 400)
                interp = 'Crisis levels'
            
            return {
                'score': round(score, 1),
                'value': round(current_spread, 2),
                'last_updated': last_updated,
                'interpretation': interp,
                'median_5y': round(hy_spread.median(), 2)
            }
        except Exception as e:
            return {'score': 0.0, 'value': None, 'interpretation': str(e)}
    
    def _score_interest_coverage(self) -> Dict[str, Any]:
        """
        Score based on median interest coverage ratios for leveraged loan borrowers
        Interest Coverage = EBITDA / Interest Expense
        """
        median_coverage = self.manual_inputs.get('leveraged_loan_coverage', 2.5)
        coverage_as_of = self.manual_inputs.get('leveraged_loan_coverage_as_of', None)
        
        if median_coverage > 3.0:
            score = 0.0
            interp = 'Healthy debt service capacity'
        elif median_coverage >= 2.5:
            score = 2.0
            interp = 'Moderate coverage - watchlist'
        elif median_coverage >= 2.0:
            score = 5.0
            interp = 'Weak coverage - rising stress'
        elif median_coverage >= 1.5:
            score = 7.0
            interp = 'Critical - minimal buffer'
        else:
            score = 10.0
            interp = 'Distressed - unsustainable debt loads'
        
        return {
            'score': round(score, 1),
            'value': round(median_coverage, 2),
            'last_updated': coverage_as_of,
            'interpretation': interp,
            'is_manual': True
        }
    
    def _score_default_momentum(self) -> Dict[str, Any]:
        """
        Score based on change in leveraged loan default rates
        Rising defaults = early warning of deterioration
        """
        default_rate = self.manual_inputs.get('leveraged_loan_default_rate', 2.0)
        default_rate_6m_ago = self.manual_inputs.get('leveraged_loan_default_rate_6m_ago', 2.0)
        default_as_of = self.manual_inputs.get('leveraged_loan_default_as_of', None)
        
        momentum = default_rate - default_rate_6m_ago
        
        if momentum >= 1.5:  # Rapid acceleration
            score = 10.0
            interp = 'Defaults accelerating rapidly'
        elif momentum >= 1.0:
            score = 7.0
            interp = 'Sharp increase in defaults'
        elif momentum >= 0.5:
            score = 4.0
            interp = 'Defaults rising steadily'
        elif momentum > 0:
            score = 2.0
            interp = 'Defaults trending up'
        else:
            score = 0.0
            interp = 'Stable or improving'
        
        return {
            'score': round(score, 1),
            'value': round(default_rate, 2),
            'momentum_6m': round(momentum, 2),
            'last_updated': default_as_of,
            'interpretation': interp,
            'is_manual': True
        }
    
    def _score_recovery_rate(self) -> Dict[str, Any]:
        """
        Score based on loan recovery rates (% recovered on defaulted loans)
        Lower recoveries = higher loss severity when defaults occur
        """
        recovery_rate = self.manual_inputs.get('leveraged_loan_recovery_rate', 65)
        recovery_as_of = self.manual_inputs.get('leveraged_loan_recovery_as_of', None)
        
        if recovery_rate >= 60:
            score = 0.0
            interp = 'Normal recovery rates'
        elif recovery_rate >= 50:
            score = 3.0
            interp = 'Below-average recoveries'
        elif recovery_rate >= 40:
            score = 6.0
            interp = 'Weak recoveries - high loss severity'
        else:
            score = 10.0
            interp = 'Crisis-level recoveries - extreme losses'
        
        return {
            'score': round(score, 1),
            'value': round(recovery_rate, 1),
            'last_updated': recovery_as_of,
            'interpretation': interp,
            'is_manual': True
        }
    
    def _score_cre_stress(self) -> Dict[str, Any]:
        """
        Category 3.3: CRE / Regional Bank Stress (0-10 points)
        
        Enhanced 4-component scoring (25% each):
        1. Delinquency rate (Manual: FDIC QBP)
        2. Regional bank stress (Automated: KRE ETF)
        3. Refinancing cliff pressure (Manual: Fed FSR)
        4. Structural vacancy stress (Manual: CBRE/CoStar)
        
        Captures the $1.2T CRE refinancing cliff risk that traditional
        delinquency metrics miss until it's too late
        """
        # Component 1: CRE Delinquency Rate (25%)
        delinq_score, delinq_data = self._score_cre_delinquency()
        
        # Component 2: Regional Bank Stress via KRE (25%)
        bank_score, bank_data = self._score_regional_bank_stress()
        
        # Component 3: Refinancing Cliff Pressure (25%)
        refi_score, refi_data = self._score_refinancing_cliff()
        
        # Component 4: Structural Vacancy Stress (25%)
        vacancy_score, vacancy_data = self._score_vacancy_stress()
        
        # Weighted combination (equal weights)
        combined_score = (
            delinq_score * 0.25 +
            bank_score * 0.25 +
            refi_score * 0.25 +
            vacancy_score * 0.25
        )
        
        # Overall interpretation
        overall_interp = self._interpret_cre_combined(combined_score)
        
        return {
            'name': 'cre_stress',
            'score': round(combined_score, 1),
            'value': delinq_data.get('value', 0),
            'last_updated': delinq_data.get('last_updated'),
            'interpretation': overall_interp,
            'data_source': 'Manual: FDIC QBP, Fed FSR + Automated: KRE',
            'is_manual': True,
            'next_update': '2026-02-15 (Next FDIC QBP)',
            'components': {
                'delinquency': {
                    'score': round(delinq_score, 1),
                    **delinq_data
                },
                'bank_stress': {
                    'score': round(bank_score, 1),
                    **bank_data
                },
                'refinancing_cliff': {
                    'score': round(refi_score, 1),
                    **refi_data
                },
                'vacancy_structural': {
                    'score': round(vacancy_score, 1),
                    **vacancy_data
                }
            }
        }
    
    def _score_cre_delinquency(self) -> tuple[float, Dict[str, Any]]:
        """Score CRE delinquency rates"""
        delinquency_rate = self.manual_inputs.get('cre_delinquency_rate', 0)
        cre_as_of = self.manual_inputs.get('cre_delinquency_as_of', None)
        
        if delinquency_rate < 3.0:
            score = 0.0
            interp = 'Low delinquency - healthy'
        elif delinquency_rate < 5.0:
            score = 3.0
            interp = 'Early deterioration'
        elif delinquency_rate < 6.0:
            score = 5.0
            interp = 'Concerning levels'
        elif delinquency_rate < 8.0:
            score = 7.0
            interp = 'Significant stress'
        else:  # >= 8.0
            score = 10.0
            interp = 'Crisis levels'
        
        return score, {
            'value': round(float(delinquency_rate), 2),
            'last_updated': cre_as_of,
            'interpretation': interp
        }
    
    def _score_regional_bank_stress(self) -> tuple[float, Dict[str, Any]]:
        """Score regional bank stress via KRE ETF"""
        try:
            if not self.yfinance:
                return 0.0, {'interpretation': 'No yfinance client'}
            
            kre = self.yfinance.get_ticker('KRE')
            hist = kre.history(period='1y')
            
            if len(hist) == 0:
                return 0.0, {'interpretation': 'No KRE data'}
            
            current_price = hist['Close'].iloc[-1]
            high_52w = hist['High'].max()
            drawdown = ((current_price - high_52w) / high_52w) * 100
            
            # Score based on drawdown
            if drawdown > -10:
                score = 0.0
                interp = 'Banks healthy'
            elif drawdown > -15:
                score = 3.0
                interp = 'Moderate stress'
            elif drawdown > -20:
                score = 5.0
                interp = 'Concerning weakness'
            elif drawdown > -30:
                score = 7.0
                interp = 'Significant stress'
            else:  # <= -30
                score = 10.0
                interp = 'Crisis levels'
            
            return score, {
                'kre_current_price': round(current_price, 2),
                'kre_52w_high': round(high_52w, 2),
                'kre_drawdown_pct': round(drawdown, 2),
                'interpretation': interp
            }
        except Exception as e:
            print(f"Warning: Error fetching KRE: {e}")
            return 0.0, {'interpretation': f'Error: {str(e)}'}
    
    def _score_refinancing_cliff(self) -> tuple[float, Dict[str, Any]]:
        """
        Score refinancing cliff pressure
        Tracks maturity wall and rate shock impact
        """
        maturing_12m = self.manual_inputs.get('cre_maturing_loans_12m', 0)
        maturing_24m = self.manual_inputs.get('cre_maturing_loans_24m', 0)
        refi_spread_shock = self.manual_inputs.get('cre_refi_spread_shock', 0)
        refi_as_of = self.manual_inputs.get('cre_refinancing_as_of', None)
        
        # Base score on 12-month maturity volume (billions)
        if maturing_12m < 200:
            score = 0.0
            interp = 'Manageable maturities'
        elif maturing_12m < 400:
            score = 3.0
            interp = 'Elevated maturities'
        elif maturing_12m < 600:
            score = 6.0
            interp = 'High refinancing pressure'
        else:  # >= 600B
            score = 10.0
            interp = 'Refinancing cliff - systemic risk'
        
        # Rate shock adjustment (bps higher than original rates)
        if refi_spread_shock > 300:  # > 3% rate shock
            score = min(10.0, score + 2.0)
            interp += ' + extreme rate shock'
        elif refi_spread_shock > 200:
            score = min(10.0, score + 1.0)
            interp += ' + significant rate shock'
        
        return score, {
            'maturing_12m_billions': float(maturing_12m),
            'maturing_24m_billions': float(maturing_24m),
            'rate_shock_bps': float(refi_spread_shock),
            'last_updated': refi_as_of,
            'interpretation': interp
        }
    
    def _score_vacancy_stress(self) -> tuple[float, Dict[str, Any]]:
        """
        Score structural vacancy stress (particularly office sector)
        High vacancy = reduced property values = harder refinancing
        """
        office_vacancy = self.manual_inputs.get('cre_office_vacancy', 12.0)
        property_value_decline = self.manual_inputs.get('cre_property_value_decline_pct', 0)
        vacancy_as_of = self.manual_inputs.get('cre_office_vacancy_as_of', None)
        
        # Score based on office vacancy rates
        if office_vacancy < 13:
            score = 0.0
            interp = 'Healthy occupancy'
        elif office_vacancy < 16:
            score = 3.0
            interp = 'Elevated vacancy'
        elif office_vacancy < 18:
            score = 6.0
            interp = 'High vacancy - structural concerns'
        else:  # >= 18% (current ~19.8%)
            score = 10.0
            interp = 'Crisis vacancy - structural decline'
        
        # Property value decline adjustment
        if property_value_decline < -25:  # > 25% decline
            score = min(10.0, score + 2.0)
            interp += ' + severe value erosion'
        elif property_value_decline < -15:
            score = min(10.0, score + 1.0)
            interp += ' + significant value decline'
        
        return score, {
            'office_vacancy_pct': round(float(office_vacancy), 1),
            'property_value_decline_pct': round(float(property_value_decline), 1),
            'last_updated': vacancy_as_of,
            'interpretation': interp
        }
    
    def _interpret_cre_combined(self, score: float) -> str:
        """Generate comprehensive CRE risk interpretation"""
        if score < 3:
            return 'Healthy CRE market - all indicators stable'
        elif score < 5:
            return 'Early warning - multiple stress indicators emerging'
        elif score < 7:
            return 'Elevated stress - refinancing challenges mounting'
        else:
            return 'Crisis conditions - systemic CRE risk across multiple dimensions'
    
    def _calculate_contagion_multiplier(
        self, 
        hedge_score: float, 
        corp_score: float, 
        cre_score: float
    ) -> float:
        """
        Calculate cross-sector contagion amplification multiplier
        
        When multiple leverage sectors are stressed simultaneously,
        systemic risk amplifies through interconnections:
        - Hedge fund deleveraging → Treasury market disruption → margin calls
        - Corporate defaults → bank losses → credit tightening
        - CRE stress → regional bank failures → credit contraction
        
        Returns:
            Multiplier from 1.0 (isolated) to 1.5 (maximum amplification)
        """
        # Count sectors with elevated stress (score >= 6)
        stressed_sectors = sum([
            hedge_score >= 6,
            corp_score >= 6,
            cre_score >= 6
        ])
        
        # Multiplier based on number of stressed sectors
        if stressed_sectors == 0:
            return 1.0  # No amplification - risks isolated
        elif stressed_sectors == 1:
            return 1.1  # Single sector - limited spillover
        elif stressed_sectors == 2:
            return 1.25  # Two sectors - cross-sector risk building
        else:  # All 3 sectors stressed
            return 1.5  # Maximum systemic amplification
    
    def _assess_systemic_level(self, score: float) -> str:
        """Assess overall systemic risk level"""
        if score < 5:
            return 'LOW - Isolated pockets only'
        elif score < 10:
            return 'MODERATE - Watchlist conditions'
        elif score < 15:
            return 'ELEVATED - Multiple vulnerabilities'
        elif score < 20:
            return 'HIGH - Systemic stress building'
        else:
            return 'CRITICAL - Crisis-level systemic risk'
    
    def _get_risk_narrative(
        self, 
        total_score: float,
        hedge_fund_score: Dict[str, Any],
        corp_credit_score: Dict[str, Any],
        cre_score: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive risk narrative based on component scores
        Provides context and sector-specific warnings
        """
        narrative_parts = []
        
        # Overall assessment
        if total_score >= 20:
            narrative_parts.append(
                "⚠️ SYSTEMIC CRISIS CONDITIONS: All three leverage sectors show "
                "severe stress. The financial system is vulnerable to cascading "
                "failures across hedge funds, corporate credit, and CRE markets."
            )
        elif total_score >= 15:
            narrative_parts.append(
                "🔴 HIGH SYSTEMIC RISK: Multiple leverage-driven vulnerabilities "
                "converging. Elevated risk of contagion across financial sectors."
            )
        elif total_score >= 10:
            narrative_parts.append(
                "🟡 ELEVATED RISK: Notable stress in at least one leverage sector. "
                "Monitoring for cross-sector spillovers required."
            )
        else:
            narrative_parts.append(
                "🟢 MANAGEABLE RISK: Leverage risks contained to isolated pockets."
            )
        
        # Sector-specific warnings
        hf_score = hedge_fund_score['score']
        if hf_score >= 8:
            hf_pct = hedge_fund_score.get('value', 0)
            narrative_parts.append(
                f"Hedge Fund Leverage ({hf_score}/10): Record levels at "
                f"{hf_pct}th percentile. "
            )
            if hedge_fund_score.get('concentration_warning'):
                narrative_parts.append(hedge_fund_score['concentration_warning'])
        
        cc_score = corp_credit_score['score']
        if cc_score >= 6:
            narrative_parts.append(
                f"Corporate Credit ({cc_score}/10): Multi-factor stress detected. "
            )
            # Add specific component warnings
            comps = corp_credit_score.get('components', {})
            if comps.get('default_momentum', {}).get('score', 0) >= 5:
                narrative_parts.append("Default momentum accelerating.")
            if comps.get('interest_coverage', {}).get('score', 0) >= 5:
                narrative_parts.append("Interest coverage deteriorating.")
        
        cre_s = cre_score['score']
        if cre_s >= 7:
            narrative_parts.append(
                f"CRE Stress ({cre_s}/10): Multi-dimensional stress. "
            )
            comps = cre_score.get('components', {})
            if comps.get('refinancing_cliff', {}).get('score', 0) >= 6:
                mat_12m = comps['refinancing_cliff'].get('maturing_12m_billions', 0)
                narrative_parts.append(
                    f"${mat_12m}B maturing within 12 months creates refinancing cliff risk."
                )
            if comps.get('vacancy_structural', {}).get('score', 0) >= 6:
                narrative_parts.append("Structural vacancy crisis in office sector.")
        
        # Interconnection warning
        stressed_count = sum([hf_score >= 6, cc_score >= 6, cre_s >= 7])
        if stressed_count >= 2:
            narrative_parts.append(
                "⚡ CONTAGION RISK: Multiple sectors stressed simultaneously. "
                "Shock in one area likely to cascade through interconnected system."
            )
        
        return " ".join(narrative_parts)
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        return CategoryMetadata(
            name='Leverage & Stability',
            max_points=25.0,
            description='Identifies hidden fragilities and systemic risks through hedge fund leverage, corporate credit (with interest coverage and default momentum), and comprehensive CRE stress (delinquency, bank stress, refinancing cliff, vacancy).',
            update_frequency='Daily (Credit Spreads, Regional Banks), Semi-annual (Hedge Fund Leverage, Corporate Metrics), Quarterly (CRE Delinquency)',
            data_sources=[
                'FRED: BAMLH0A0HYM2',
                'Yahoo Finance: KRE',
                'Manual: Fed FSR (Leverage, Corporate Metrics)',
                'Manual: FDIC QBP (CRE Delinquency)',
                'Manual: Market Data (CRE Refinancing, Vacancy)'
            ],
            next_update='2026-02-15 (FDIC Quarterly Banking Profile)'
        )


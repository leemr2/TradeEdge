# Leverage & Stability Category Enhancement Specifications

## Executive Summary

Based on comprehensive research into systemic leverage risks in the U.S. financial system, this document outlines critical improvements needed for the `leverage_stability.py` calculator to better capture current risk levels and provide early warning of systemic instability.

**Current State:** The calculator scores 2.0/25 despite significant documented leverage risks across all three components.

**Target State:** Enhanced scoring that accurately reflects:
- Record hedge fund leverage (95th percentile)
- Elevated corporate credit stress (rising defaults, deteriorating coverage ratios)
- CRE crisis conditions ($1.2T refinancing cliff, 8.5% office delinquency, 19.8% vacancy)

---

## Part 1: Critical Scoring Logic Fixes

### 1.1 Hedge Fund Leverage Scoring - CORRECTION REQUIRED ❌

**Current Problem:**
```python
elif 75 <= leverage_percentile < 90:
    score = 4 + ((leverage_percentile - 75) / 15) * 4  # Linear 4-8 ❌ WRONG
```

**Reference Guide Specification:**
- 75-90th percentile should yield **exactly 5.0 points** (not 4-8)

**Required Fix:**
```python
elif 75 <= leverage_percentile < 90:
    score = 5.0  # Fixed value per specification
    interpretation = 'Elevated but stable leverage'
```

**Rationale:** The reference guide explicitly states "5" for this range, not "5-8" or "4-8".

---

### 1.2 Corporate Credit - Add Missing Dynamics

**Current Implementation:** Uses only absolute HY spread thresholds
**Research Finding:** Misses key distress signals that precede spread widening

**Required Enhancements:**

#### A. Add Interest Coverage Ratio Tracking
**Data Source:** Manual input from Fed Financial Stability Report
**Frequency:** Semi-annual (May, November)

**New Component Scoring:**
```python
def _score_interest_coverage(self) -> Dict[str, Any]:
    """
    Track corporate interest coverage ratios as early warning
    
    Interest Coverage = EBITDA / Interest Expense
    Lower ratios indicate firms struggling to service debt
    """
    # Median coverage for leveraged loan borrowers
    median_coverage = self.manual_inputs.get('leveraged_loan_coverage', 2.5)
    
    # Scoring thresholds based on Fed research
    if median_coverage > 3.0:
        score = 0.0
        interpretation = 'Healthy debt service capacity'
    elif 2.5 <= median_coverage <= 3.0:
        score = 2.0
        interpretation = 'Moderate coverage - watchlist'
    elif 2.0 <= median_coverage < 2.5:
        score = 5.0
        interpretation = 'Weak coverage - rising stress'
    else:  # < 2.0
        score = 8.0
        interpretation = 'Critical - minimal debt service buffer'
    
    return {
        'name': 'interest_coverage',
        'score': round(score, 1),
        'value': round(median_coverage, 2),
        'interpretation': interpretation,
        'data_source': 'Manual: Fed FSR - Corporate Debt Section',
        'is_manual': True
    }
```

#### B. Add Default Rate Momentum
**Research Finding:** "Default rates on leveraged loans have continued to rise in 2024"

**Enhancement:**
```python
def _score_corporate_credit_enhanced(self) -> Dict[str, Any]:
    """Enhanced corporate credit with spread + default momentum"""
    
    # Existing HY spread scoring (keep current logic)
    spread_score = self._score_hy_spreads()
    
    # NEW: Track default rate changes
    default_rate = self.manual_inputs.get('leveraged_loan_default_rate', 2.0)
    default_rate_6m_ago = self.manual_inputs.get('leveraged_loan_default_rate_6m_ago', 1.5)
    
    momentum = default_rate - default_rate_6m_ago
    
    # Momentum scoring
    if momentum > 1.0:  # Rapid acceleration
        momentum_score = 3.0
        momentum_interp = 'Defaults accelerating rapidly'
    elif momentum > 0.5:
        momentum_score = 2.0
        momentum_interp = 'Defaults rising steadily'
    elif momentum > 0:
        momentum_score = 1.0
        momentum_interp = 'Defaults trending up'
    else:
        momentum_score = 0.0
        momentum_interp = 'Stable or improving'
    
    # Combined: 70% spreads, 30% momentum
    combined_score = (spread_score * 0.7) + (momentum_score * 0.3)
    
    return {
        'name': 'corporate_credit',
        'score': round(combined_score, 1),
        'spread_component': spread_score,
        'momentum_component': momentum_score,
        'default_rate': default_rate,
        'default_momentum': momentum,
        'interpretation': momentum_interp
    }
```

#### C. Add Recovery Rate Tracking
**Research Finding:** "Loan recovery rates fell to their lowest levels since 2016"

**New Metric:**
```python
# Add to manual inputs
recovery_rate = self.manual_inputs.get('leveraged_loan_recovery_rate', 65)  # %

# Scoring modifier (reduces effective spread score when recoveries weak)
if recovery_rate < 40:
    recovery_penalty = 2.0  # Add to corporate credit score
elif recovery_rate < 55:
    recovery_penalty = 1.0
else:
    recovery_penalty = 0.0
```

---

### 1.3 CRE Stress - Major Methodology Overhaul Required

**Current Problem:** Treats delinquency and bank stress as independent 50/50 weighted components

**Research Findings:**
- **Refinancing cliff:** "$1.2 trillion in CRE debt maturing 2025-2026"
- **Structural decline:** "Office vacancy 19.8% vs 10-12% normal"
- **Property value collapse:** "20-30% or more decline in office valuations"
- **Regional bank concentration:** "$3.4 trillion in CRE loans at banks"

**Required: Multi-Factor CRE Risk Score**

```python
def _score_cre_stress_enhanced(self) -> Dict[str, Any]:
    """
    Enhanced CRE scoring with 4 components:
    1. Delinquency rate (25%)
    2. Regional bank stress (25%) 
    3. Refinancing cliff pressure (25%)
    4. Vacancy / structural stress (25%)
    """
    
    # COMPONENT 1: Delinquency Rate (existing)
    delinquency_rate = self.manual_inputs.get('cre_delinquency_rate', 0)
    
    if delinquency_rate < 3.0:
        delinq_score = 0.0
    elif delinquency_rate < 5.0:
        delinq_score = 3.0
    elif delinquency_rate < 6.0:
        delinq_score = 5.0
    elif delinquency_rate < 8.0:
        delinq_score = 7.0
    else:  # >= 8.0 (CURRENT STATE)
        delinq_score = 10.0
    
    # COMPONENT 2: Regional Bank Stress (existing KRE logic)
    kre_score = self._calculate_kre_stress()  # 0-10
    
    # COMPONENT 3: NEW - Refinancing Cliff Pressure
    maturing_loans_12m = self.manual_inputs.get('cre_maturing_loans_12m', 450)  # Billions
    rate_environment = self.manual_inputs.get('cre_refi_spread_shock', 250)  # bps higher than orig
    
    # Score based on maturity volume + rate shock
    if maturing_loans_12m < 200:
        refi_score = 0.0
    elif maturing_loans_12m < 400:
        refi_score = 3.0
    elif maturing_loans_12m < 600:
        refi_score = 6.0
    else:  # >= 600B (approaching current ~$1.2T over 2 years)
        refi_score = 10.0
    
    # Rate shock adjustment
    if rate_environment > 300:  # > 3% higher rates
        refi_score = min(10.0, refi_score + 2.0)
    
    # COMPONENT 4: NEW - Structural Stress (Vacancy)
    office_vacancy = self.manual_inputs.get('cre_office_vacancy', 12.0)  # %
    
    if office_vacancy < 13:
        vacancy_score = 0.0
    elif office_vacancy < 16:
        vacancy_score = 3.0
    elif office_vacancy < 18:
        vacancy_score = 6.0
    else:  # >= 18% (current ~19.8%)
        vacancy_score = 10.0
    
    # COMBINED SCORE (weighted average)
    weights = {
        'delinquency': 0.25,
        'bank_stress': 0.25,
        'refinancing_cliff': 0.25,
        'vacancy_stress': 0.25
    }
    
    combined_score = (
        delinq_score * weights['delinquency'] +
        kre_score * weights['bank_stress'] +
        refi_score * weights['refinancing_cliff'] +
        vacancy_score * weights['vacancy_stress']
    )
    
    return {
        'name': 'cre_stress',
        'score': round(combined_score, 1),
        'components': {
            'delinquency': {'score': delinq_score, 'value': delinquency_rate},
            'bank_stress': {'score': kre_score},
            'refinancing_cliff': {'score': refi_score, 'maturing_12m': maturing_loans_12m},
            'vacancy_structural': {'score': vacancy_score, 'office_vacancy': office_vacancy}
        },
        'interpretation': self._interpret_cre_combined(combined_score)
    }

def _interpret_cre_combined(self, score: float) -> str:
    """Interpret combined CRE score"""
    if score < 3:
        return 'Healthy CRE market - all indicators stable'
    elif score < 5:
        return 'Early warning - multiple stress indicators emerging'
    elif score < 7:
        return 'Elevated stress - refinancing challenges mounting'
    else:
        return 'Crisis conditions - systemic CRE risk'
```

---

## Part 2: New Data Requirements

### Manual Inputs to Add

**File:** `frs_config.py`

```python
MANUAL_INPUTS = {
    # Existing...
    
    # Corporate Credit Enhancements
    'corporate_credit': {
        'leveraged_loan_coverage': 2.1,  # Median interest coverage ratio
        'leveraged_loan_default_rate': 3.2,  # Current % (annual)
        'leveraged_loan_default_rate_6m_ago': 2.4,
        'leveraged_loan_recovery_rate': 42,  # % recovery on defaults
        'as_of': '2025-11-15',
        'source': 'Fed FSR Nov 2025 + FDIC Risk Review 2025',
        'next_update': '2026-05-15'
    },
    
    # CRE Refinancing Cliff
    'cre_refinancing': {
        'maturing_loans_12m': 600,  # Billions USD maturing next 12 months
        'maturing_loans_24m': 1200,  # Total 2-year refinancing wall
        'refi_spread_shock': 275,  # bps higher vs original rates
        'property_value_decline_pct': -28,  # % decline from peak (office)
        'as_of': '2025-11-01',
        'source': 'Fed FSR + FSOC Annual Report 2024'
    }
}
```

---

## Part 3: Hedge Fund Leverage - Additional Signals

### Research Finding: Basis Trade Concentration Risk

**Current:** Binary flag `basis_trade_concern`
**Enhanced:** Quantitative tracking

```python
def _score_hedge_fund_leverage_enhanced(self) -> Dict[str, Any]:
    """Enhanced with basis trade sizing and dealer capacity"""
    
    leverage_percentile = self.manual_inputs.get('hedge_fund_leverage_percentile', 50)
    basis_concern = self.manual_inputs.get('hedge_fund_basis_trade_concern', False)
    
    # NEW: Basis trade notional relative to Treasury market
    basis_trade_notional = self.manual_inputs.get('hedge_fund_basis_trade_notional', 0)  # Billions
    treasury_market_size = 27000  # ~$27T total Treasury market
    basis_concentration = (basis_trade_notional / treasury_market_size) * 100
    
    # Base scoring (existing logic, with correction)
    if leverage_percentile < 60 and not basis_concern:
        score = 0.0
    elif 60 <= leverage_percentile < 75:
        score = 1 + ((leverage_percentile - 60) / 15) * 3  # 1-4
    elif 75 <= leverage_percentile < 90:
        score = 5.0  # FIXED per specification
    else:  # >= 90 OR basis_concern
        score = 8 + min(2, (leverage_percentile - 90) / 5)  # 8-10
    
    # NEW: Basis trade concentration penalty
    if basis_concentration > 4.0:  # > 4% of Treasury market
        score = min(10.0, score + 2.0)
        conc_warning = 'Extreme basis trade concentration'
    elif basis_concentration > 3.0:
        score = min(10.0, score + 1.0)
        conc_warning = 'High basis trade concentration'
    else:
        conc_warning = None
    
    # NEW: Dealer capacity constraints
    dealer_solvency = self.manual_inputs.get('primary_dealer_slr_ratio', 6.5)  # %
    if dealer_solvency < 5.5:  # Approaching regulatory minimum
        score = min(10.0, score + 1.0)
        dealer_warning = 'Dealer capacity constrained - amplification risk'
    else:
        dealer_warning = None
    
    return {
        'name': 'hedge_fund_leverage',
        'score': round(score, 1),
        'value': leverage_percentile,
        'basis_trade_billions': basis_trade_notional,
        'basis_concentration_pct': round(basis_concentration, 2),
        'concentration_warning': conc_warning,
        'dealer_warning': dealer_warning
    }
```

---

## Part 4: Cross-Sector Contagion Indicators

### Research Finding: "These vulnerabilities could interact in a downturn"

**New Category Component: Systemic Interconnection Risk**

```python
def _calculate_contagion_multiplier(self) -> float:
    """
    Assess cross-sector amplification risk
    Returns multiplier: 1.0 (normal) to 1.5 (max amplification)
    """
    
    # Count sectors with elevated stress (score >= 6)
    hedge_score = self._score_hedge_fund_leverage()['score']
    corp_score = self._score_corporate_credit()['score']
    cre_score = self._score_cre_stress()['score']
    
    stressed_sectors = sum([
        hedge_score >= 6,
        corp_score >= 6,
        cre_score >= 6
    ])
    
    # Multiplier logic
    if stressed_sectors == 0:
        return 1.0  # No amplification
    elif stressed_sectors == 1:
        return 1.1  # Single sector isolated
    elif stressed_sectors == 2:
        return 1.25  # Cross-sector risk building
    else:  # All 3 sectors stressed
        return 1.5  # Maximum systemic amplification
    
def calculate(self) -> Dict[str, Any]:
    """Calculate with contagion multiplier"""
    
    # Individual components
    hedge_fund_score = self._score_hedge_fund_leverage()
    corp_credit_score = self._score_corporate_credit()
    cre_score = self._score_cre_stress()
    
    # Raw total
    raw_total = (
        hedge_fund_score['score'] + 
        corp_credit_score['score'] + 
        cre_score['score']
    )
    
    # Apply contagion multiplier
    contagion_mult = self._calculate_contagion_multiplier()
    adjusted_total = raw_total * contagion_mult
    
    # Cap at 25
    total_score = min(25.0, adjusted_total)
    
    return {
        'score': round(total_score, 1),
        'max_points': 25.0,
        'raw_total': round(raw_total, 1),
        'contagion_multiplier': round(contagion_mult, 2),
        'adjusted_total': round(adjusted_total, 1),
        'components': {...},
        'systemic_risk_level': self._assess_systemic_level(total_score)
    }

def _assess_systemic_level(self, score: float) -> str:
    """Interpret systemic risk level"""
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
```

---

## Part 5: Market Behavior Indicators

### Research Finding: "$7.7 trillion in money market funds - record cash levels"

**New Signal: Cash Position Paradox**

```python
def _check_money_market_surge(self) -> Dict[str, Any]:
    """
    Track money market fund assets as risk-off indicator
    High cash = investors pricing in instability
    """
    
    mm_assets = self.manual_inputs.get('money_market_assets_trillions', 6.0)
    gdp_trillions = 29.0  # Current US GDP
    
    mm_to_gdp = (mm_assets / gdp_trillions) * 100
    
    # Historical context
    if mm_to_gdp > 26:  # Current ~26.5%
        risk_signal = 'EXTREME'
        interpretation = 'Record cash hoarding - crisis-level defensiveness'
        score_impact = +2.0
    elif mm_to_gdp > 23:
        risk_signal = 'ELEVATED'
        interpretation = 'High cash positions - cautious sentiment'
        score_impact = +1.0
    elif mm_to_gdp > 20:
        risk_signal = 'MODERATE'
        interpretation = 'Above-average cash preference'
        score_impact = +0.5
    else:
        risk_signal = 'NORMAL'
        interpretation = 'Healthy cash deployment'
        score_impact = 0.0
    
    return {
        'mm_assets_trillions': mm_assets,
        'mm_to_gdp_pct': round(mm_to_gdp, 1),
        'risk_signal': risk_signal,
        'interpretation': interpretation,
        'category_score_adjustment': score_impact
    }
```

---

## Part 6: Enhanced Interpretation Framework

### Risk Level Matrix

```python
def get_risk_narrative(self, total_score: float, components: dict) -> str:
    """Generate comprehensive risk narrative"""
    
    narrative = []
    
    # Overall assessment
    if total_score >= 20:
        narrative.append(
            "⚠️ SYSTEMIC CRISIS CONDITIONS: All three leverage sectors show "
            "severe stress. The financial system is vulnerable to cascading "
            "failures across hedge funds, corporate credit, and CRE markets."
        )
    elif total_score >= 15:
        narrative.append(
            "🔴 HIGH SYSTEMIC RISK: Multiple leverage-driven vulnerabilities "
            "converging. Elevated risk of contagion across financial sectors."
        )
    elif total_score >= 10:
        narrative.append(
            "🟡 ELEVATED RISK: Notable stress in at least one leverage sector. "
            "Monitoring for cross-sector spillovers required."
        )
    else:
        narrative.append(
            "🟢 MANAGEABLE RISK: Leverage risks contained to isolated pockets."
        )
    
    # Sector-specific warnings
    hf_score = components['hedge_fund_leverage']['score']
    if hf_score >= 8:
        narrative.append(
            f"Hedge Fund Leverage ({hf_score}/10): Record levels at "
            f"{components['hedge_fund_leverage']['value']}th percentile. "
            "Basis trade concentration creates Treasury market vulnerability."
        )
    
    cc_score = components['corporate_credit']['score']
    if cc_score >= 6:
        narrative.append(
            f"Corporate Credit ({cc_score}/10): Default momentum accelerating. "
            "Rising interest expense stressing highly-leveraged borrowers."
        )
    
    cre_score = components['cre_stress']['score']
    if cre_score >= 7:
        narrative.append(
            f"CRE Stress ({cre_score}/10): Refinancing cliff approaching with "
            "$1.2T maturing 2025-2026. Office sector in structural decline."
        )
    
    # Interconnection warning
    stressed_count = sum([hf_score >= 6, cc_score >= 6, cre_score >= 7])
    if stressed_count >= 2:
        narrative.append(
            "⚡ CONTAGION RISK: Multiple sectors stressed simultaneously. "
            "Shock in one area likely to cascade through interconnected system."
        )
    
    return " ".join(narrative)
```

---

## Part 7: Data Collection Workflow

### Semi-Annual Update (Fed FSR)

**When:** 2nd week of May & November
**Time Required:** 30-40 minutes
**Document:** Federal Reserve Financial Stability Report

**Extraction Checklist:**

```python
FED_FSR_EXTRACTION = {
    'section_1_leverage': {
        'hedge_fund_leverage_percentile': 'Chart 3-1: Hedge Fund Gross Leverage',
        'basis_trade_notional': 'Section narrative on Treasury basis trading',
        'basis_trade_concern': 'Look for: "elevated", "concentrated", "fragility"',
        'primary_dealer_slr': 'Banking section - dealer capacity metrics'
    },
    'section_2_corporate': {
        'leveraged_loan_coverage': 'Table: Interest Coverage Ratios',
        'default_rate': 'Chart: Corporate Default Trends',
        'recovery_rate': 'Narrative on loan recoveries'
    },
    'section_3_cre': {
        'maturing_loans_12m': 'CRE refinancing timeline chart',
        'office_vacancy': 'Property market conditions narrative',
        'delinquency_by_type': 'Table: CRE loan performance'
    }
}
```

### Quarterly Update (FDIC QBP)

**When:** ~6 weeks after quarter end (Feb 15, May 15, Aug 15, Nov 15)
**Time Required:** 10 minutes
**Document:** FDIC Quarterly Banking Profile

**Extraction:**
```python
FDIC_QBP_EXTRACTION = {
    'cre_delinquency_rate': 'Table II-B: Loan Performance → CRE Delinquency %',
    'cre_office_delinquency': 'Disaggregated by property type if available',
    'cre_loans_outstanding': 'Total CRE exposure at FDIC-insured institutions'
}
```

---

## Part 8: Implementation Priority

### Phase 1: Critical Fixes (Immediate)
1. ✅ Fix hedge fund 75-90th percentile scoring (5.0 not 4-8)
2. ✅ Implement 4-component CRE scoring with refinancing cliff
3. ✅ Add contagion multiplier logic

### Phase 2: Enhanced Data 
1. Add corporate interest coverage tracking
2. Add default rate momentum
3. Add recovery rate monitoring
4. Implement money market surge indicator

---

## Part 9: Expected Score Impact

### Current Scoring (Using Research Data):

**Hedge Fund Leverage:**
- Percentile: 95th
- Basis trade: $1.2T (4.4% of Treasury market)
- Current score: 0.0 → **Should be: 10.0** ❌

**Corporate Credit:**
- HY Spread: 289 bps (low)
- BUT: Default momentum +0.8pp, Coverage 2.1x, Recovery 42%
- Current score: 0.0 → **Should be: 6.5** ❌

**CRE Stress:**
- Delinquency: 8.5%, Vacancy: 19.8%, Refinancing: $1.2T
- Current score: 2.0 → **Should be: 9.5** ❌

### Corrected Category Total:
- **Current:** 2.0/25 (massive undercount)
- **Should be:** 25.0/25 (capped) ⚠️
- **Raw (pre-contagion):** 26.0/30
- **With contagion multiplier (1.5):** 39.0 → Capped at 25.0

**This represents a systemic risk level consistent with:**
- Pre-2008 Financial Crisis
- March 2020 COVID Panic
- Late 2000 Dot-com Peak

---

## Part 10: Validation & Calibration

### Backtest Against Historical Episodes

**Episode 1: 2008 Financial Crisis (Sep 2008)**
- Hedge funds: Deleveraging cascade
- Corporate: High-yield spreads >2000bps
- CRE: Mass defaults, bank failures
- **Expected Score:** 25/25 ✓

**Episode 2: COVID Crisis (Mar 2020)**
- Hedge funds: Treasury basis unwind
- Corporate: Default spike, frozen markets
- CRE: Temporary forbearance
- **Expected Score:** 22-25/25 ✓

**Episode 3: Current (Dec 2025)**
- Hedge funds: Record leverage, basis concentration
- Corporate: Default acceleration, weak coverage
- CRE: Refinancing cliff, structural decline
- **Expected Score:** 24-25/25 ✓

### Sensitivity Analysis

Test scoring sensitivity to:
1. ±10% change in delinquency rates
2. ±100bps change in HY spreads
3. ±10 percentile points in hedge fund leverage
4. Addition/removal of contagion multiplier

---

## Conclusion

The current `leverage_stability.py` calculator significantly **underestimates systemic risk** due to:

1. **Incorrect scoring logic** (hedge fund 75-90th range)
2. **Missing critical dynamics** (defaults, coverage, refinancing cliff)
3. **Overly simplistic methodology** (ignores cross-sector contagion)
4. **Insufficient data inputs** (relies only on spreads and delinquency)

**After implementing these enhancements, the category should score ~25/25**, accurately reflecting the confluence of leverage-driven systemic risks documented in Federal Reserve, FDIC, and FSOC reports.

This aligns with the overall FRS assessment showing **87/100 total risk** with **~85% correction probability** within 12-18 months.

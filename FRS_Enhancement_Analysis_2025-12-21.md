# FRS Enhancement Specifications - Analysis & Recommendations

**Analysis Date**: December 21, 2025
**Document Analyzed**: `backend/FRS_Enhancement_Specifications.md`
**Analyst**: Claude Code (Sonnet 4.5)

---

## 📊 Overall Assessment: 7.2/10

**Verdict**: **APPROVE WITH MODIFICATIONS** - This is a well-researched, thoughtfully designed enhancement that addresses real blind spots in the current FRS system. However, critical changes are needed before implementation.

---

## 🎯 Executive Summary

### Strengths ✅
- Comprehensive, implementation-ready specification with production code
- Excellent choice of leading indicators (ISM gap, jobless claims, housing permits)
- Strong alignment with existing TradeEdge modular architecture
- Solid reliance on FRED API (11/13 indicators) for data reliability
- Clear historical context for each indicator with crisis examples

### Critical Issues ⚠️
1. **VP weight reduction too severe** (35% → 15% is a 57% cut to tactical warning capability)
2. **No systematic backtesting** (unvalidated whether new formula outperforms current CMDS)
3. **MOVE Index reliability** (Yahoo Finance is unreliable; need FRED alternative)
4. **Missing operational guidance** (no data freshness monitoring, update schedules, fallback strategies)
5. **Regime change risk** (thresholds may not adapt to changing market conditions)

---

## 📈 Detailed Analysis by Dimension

### 1. Technical Accuracy: 8/10 ✅

**Strong indicators selected**:
- ISM New Orders vs Inventories: Proven 6-9 month leading indicator
- Jobless claims trend: Excellent early labor market signal
- Dollar strength + EM stress: Captures global risk transmission
- Credit card delinquency: Best consumer stress early warning

**Issues**:
- Dollar strength thresholds arbitrary (DXY > 115 = crisis - based on what?)
- Auto delinquency uses DRALACBS (all consumer loans) as proxy, not true auto data
- Housing permits YoY can be noisy with seasonal factors

**Recommendation**: Add threshold calibration methodology section showing historical distribution analysis.

---

### 2. CMDS Formula Changes: 6/10 ⚠️

**Current**: `CMDS = (0.65 × FRS) + (0.35 × VP)`
**Proposed**: `CMDS = (0.65 × FRS) + (0.20 × EWS_normalized) + (0.15 × VP)`

**Critical concern**: VP weight drops from 35% to 15% (-57%)

In the current TradeEdge system:
- **FRS**: 12-18 month strategic risk assessment
- **VP**: 2-5 day tactical warning signals
- **EWS (new)**: 3-12 month early warning signals

**Problem**: Cutting VP by 57% severely diminishes short-term risk detection capability. VP is critical for timing precision - this may reduce the system's ability to warn of imminent volatility spikes.

**Recommended alternative formula**:
```
CMDS = (0.60 × FRS) + (0.20 × EWS_normalized) + (0.20 × VP)
```

**Rationale**:
- FRS maintains majority (60%) as fundamental foundation
- EWS gets meaningful weight (20%) for early warnings
- VP retains sufficient weight (20%) for tactical timing
- Better balance across all three timeframes: strategic/early-warning/tactical

**Missing validation**: No backtesting showing new formula would have performed better in 2008, 2018, 2020, or 2022 market events.

---

### 3. Data Source Reliability: 7/10 ✅

**FRED API (11/13 indicators)**: ✅ Excellent
- Highly reliable official government data
- Consistent update schedules
- Already integrated in TradeEdge

**Yahoo Finance (MOVE Index)**: ⚠️ CRITICAL ISSUE
- Document specifies MOVE Index via Yahoo Finance `^MOVE`
- Yahoo Finance data quality is questionable for this series
- **Alternative**: Use FRED-based Treasury stress indicators:
  - `BAMLH0A0HYM2` (High Yield spread as stress proxy)
  - `T10Y3M` (10Y-3M Treasury spread for yield curve stress)
  - `TEDRATE` (TED spread for interbank stress)

**Missing considerations**:
- No handling of data revisions (initial claims, GDP get heavily revised)
- No data validation or outlier detection mechanisms
- No fallback strategies if FRED API fails

**Recommendation**: Replace MOVE Index with FRED-based Treasury stress composite.

---

### 4. Implementation Feasibility: 8/10 ✅

**Excellent architecture fit**:
- New categories align perfectly with TradeEdge's modular category system
- Can implement as: `categories/global_contagion.py`, `categories/leading_indicators.py`, etc.
- FRED integration already exists via `fred_client.py`

**Integration issues**:

1. **Market data routing** ⚠️
   - Document doesn't account for TradeEdge's Alpha Vantage primary / Yahoo fallback strategy
   - EEM (EM equity) should route through `market_data_manager.py`, not direct Yahoo access

2. **Missing caching specifications** ⚠️
   - No TTL (time-to-live) values specified
   - **Recommendation**: Add caching TTL table:
     - Daily indicators (DXY, EM spreads): 24-hour TTL
     - Weekly (NFCI, Fed BS, claims): 7-day TTL
     - Monthly (ISM, permits, savings): 30-day TTL
     - Quarterly (delinquencies): 90-day TTL

3. **API versioning needed** ⚠️
   - New CMDS formula is a breaking change
   - **Recommendation**: Version the endpoint:
     - Keep `/api/cmds` with current formula (backward compatible)
     - Add `/api/cmds?version=2` with new formula
     - Or create `/api/cmds/v2` endpoint

4. **Missing testing strategy** ❌
   - No unit test specifications
   - No integration test guidance
   - No validation strategy
   - **Recommendation**: Add testing section with unit/integration/validation test requirements

---

### 5. Code Quality: 7/10 ✅

**Strengths**:
- Comprehensive Python examples for every indicator
- Clear calculation logic with step-by-step methodology
- Consistent function signatures

**Critical gaps**:

1. **No error handling** ❌
```python
# Current code (no error handling):
dxy = fred.get_series('DTWEXBGS')

# Recommended:
try:
    dxy = fred.get_series('DTWEXBGS', observation_start='2023-01-01')
    if dxy.empty or len(dxy) < 63:
        raise ValueError("Insufficient DXY data")
except Exception as e:
    logger.warning(f"DXY fetch failed: {e}")
    return (0, {"error": str(e), "fallback": True})
```

2. **No input validation** ❌
```python
# Add validation:
def score_dollar_strength(fred_api_key: str) -> tuple:
    if not fred_api_key or len(fred_api_key) < 20:
        raise ValueError("Invalid FRED API key")
    # ... calculation ...
    assert 0 <= score <= 5, f"Score {score} out of range"
    return score, data
```

3. **Hardcoded thresholds** ⚠️
```python
# Extract to configuration:
THRESHOLDS = {
    'dxy_crisis': 115,
    'dxy_stress': 110,
    'dxy_moderate': 105,
    'savings_rate_historical_avg': 7.0,
    'ism_gap_recession': -10
}
```

4. **Missing type hints** ⚠️
```python
from typing import Dict, Tuple

def score_dollar_strength(fred_api_key: str) -> Tuple[float, Dict[str, any]]:
    """
    Returns:
        Tuple of (score, data_dict)
        - score: float between 0-5
        - data_dict: current_dxy, change_3m_pct, percentile_2y, etc.
    """
```

5. **No logging** ❌
```python
logger.info(f"Calculating Dollar Strength: DXY={current_dxy:.2f}, 3M Δ={change_3m:.2f}%")
logger.debug(f"Components: level={level_score}, momentum={momentum_score}")
```

---

### 6. Methodology Soundness: 7/10 ✅

**Strengths**:
- Multi-factor approach (levels + rate of change)
- Uses percentiles and historical context
- Smoothing techniques (3-month averages, 4-week MAs)

**Concerns**:

1. **Inconsistent lookback periods** ⚠️
   - Dollar Strength: 2 years for percentile
   - EM Stress: 2022-01-01 start (3 years)
   - ISM Gap: 2022-01-01 start
   - Jobless Claims: 1 year for trough
   - **Recommendation**: Standardize:
     - Daily/Weekly: 2-3 year lookback
     - Monthly: 3-5 year lookback
     - Quarterly: 5-10 year lookback

2. **Threshold justification missing** ⚠️
   - Many thresholds appear arbitrary
   - Example: DXY > 115 = crisis (why 115?)
   - Example: Jobless claims +35% from trough = recession (statistical basis?)
   - **Recommendation**: Add "Threshold Calibration Methodology" showing historical distribution analysis

3. **Linear scoring only** ⚠️
   - All scoring uses linear/piecewise linear functions
   - But crisis dynamics are often non-linear (exponential deterioration)
   - Example: Fed QT impact is non-linear
   - **Recommendation**: Consider non-linear transformations for some indicators

4. **Interaction effects ignored** ⚠️
   - Indicators treated independently
   - But high dollar strength + EM stress is worse than sum
   - Rising claims + falling housing = multiplicative risk
   - Current: EWS = simple sum of 4 categories
   - **Recommendation**: Consider adding "Crisis Amplification Factor" when 3+ categories elevated

---

### 7. Historical Validation: 5/10 ⚠️

**Provided**: Excellent anecdotal historical context for each indicator
- Dollar crises: 1997 Asia, 2008 GFC, 2015 China, 2022 rate hikes
- EM stress events documented
- ISM, claims, housing historical examples

**Missing**: Systematic validation ❌

**Critical gap**: Would the new EWS have predicted major market events?

**Required backtesting**:
1. **2007-2008 Financial Crisis**:
   - Would EWS have warned 6-12 months early?
   - Which categories would have triggered?
   - How many months lead time?

2. **2018 Q4 Correction**:
   - Fed tightening + trade war
   - Would EWS have detected stress?

3. **2020 COVID Crash**:
   - Likely unpredictable (exogenous shock)
   - But document should acknowledge this limitation

4. **2022 Bear Market**:
   - Inflation + rate hikes
   - Consumer stress + housing + Fed BS indicators should have warned

**Recommendation**: Add "Historical Validation" section:
```markdown
## Historical Backtesting

### 2007-2008 Financial Crisis
- **6 months before (Mar 2008)**:
  - Consumer Stress: 7/10 (CC delinq rising, savings declining)
  - Leading Indicators: 6/10 (ISM gap negative, housing permits -30%)
  - Liquidity Plumbing: 5/10 (NFCI tightening)
  - **Total EWS: 28/40 (Elevated zone)**
- **12 months before (Sep 2007)**:
  - Total EWS: 22/40 (Moderate zone)
- **Conclusion**: EWS would have provided 6-12 month early warning
```

**Also missing**:
- Sensitivity analysis (threshold variations ±20%)
- False positive analysis (when EWS high but no crash - e.g., 2015-2016)
- Correlation analysis between the 4 EWS categories

---

### 8. Operational Readiness: 4/10 ❌

**Biggest gap in the specification**. Document focuses on implementation but ignores ongoing operations.

**Missing sections**:

1. **Data Freshness Monitoring** ❌
```python
def check_data_freshness(series_id: str, expected_freq: str) -> bool:
    """Verify data is current based on expected frequency."""
    last_update = get_last_update_date(series_id)
    days_stale = (datetime.now() - last_update).days

    thresholds = {'daily': 2, 'weekly': 8, 'monthly': 35, 'quarterly': 100}
    return days_stale <= thresholds.get(expected_freq, 7)
```

2. **Update Schedule Table** ❌
| Indicator | Frequency | Update Window | Release Delay |
|-----------|-----------|---------------|---------------|
| Dollar Strength | Daily | After 6 PM ET | Same day |
| EM Spreads | Daily | After 6 PM ET | Same day |
| NFCI | Weekly | Fridays | Same week |
| ISM | Monthly | 1st business day | Same month |
| Jobless Claims | Weekly | Thu 8:30 AM | 5 days |
| Housing Permits | Monthly | ~18th | ~45 days |
| Delinquencies | Quarterly | ~6 weeks post-qtr | 45-60 days |

3. **Threshold Review Policy** ❌
   - When to recalibrate thresholds?
   - **Recommendation**: Annual review + triggered review if 3+ consecutive months at extreme

4. **Fallback Strategies** ❌
   - What if FRED API down? → Manual entry from Fed websites
   - What if Yahoo Finance MOVE missing? → Use BAMLH0A0HYM2 (HY spread) as proxy

5. **Alerting Logic** ❌
   - When to notify users?
   - **Recommendation**:
     - Alert on zone transitions (Low → Moderate → Elevated)
     - Alert on rapid changes (>10 point move in 7 days)
     - Alert on data staleness (key indicator >30 days old)

6. **Performance SLAs** ❌
   - EWS calculation: <5 sec (fresh cache), <30 sec (cold cache)
   - API response: <500ms for `/api/ews`

---

### 9. User Experience: 6/10 ⚠️

**Cognitive load concern**: Users now track 4 scores:
- FRS (0-100)
- EWS (0-40)
- VP (0-100)
- CMDS (0-100)

**Issue**: Information overload for retail investors

**Recommendations**:

1. **Simplify user-facing presentation**:
   - Primary: CMDS only (familiar 0-100 scale)
   - Secondary: FRS/EWS/VP as drill-down components
   - Tertiary: Category breakdowns (advanced users)

2. **Improve category naming**:
   - "Liquidity Plumbing" → "Market Stress Indicators" (less jargon)
   - "Global Contagion" → "International Risk"

3. **Add actionable guidance**:
   - Current: "Elevated Risk → Reduce risk, add hedges (50-70% equity)"
   - Better: Specific actions:
     - Reduce equity allocation by 10-20%
     - Add defensive sectors (utilities, staples)
     - Consider put options or VIX calls
     - Raise cash to 20-30%

4. **Change tracking**:
   - Show week-over-week changes ("+5 points")
   - Highlight largest movers ("Consumer Stress +3")
   - Alert on threshold crossings

5. **Historical context UI**:
   - Sparkline chart (last 12 months)
   - Percentile ranking: "EWS at 75th percentile of last 2 years"
   - Crisis comparison: "Current EWS (25) similar to late 2018 (27)"

---

### 10. Blind Spots: 6/10 ⚠️

**What's missing from risk coverage?**

1. **Derivatives / Options Market Stress** ❌
   - VIX term structure (contango vs backwardation)
   - Options skew indicators
   - **Recommendation**: Add to Liquidity Plumbing category

2. **Equity Market Internals** ❌
   - Advance-Decline line
   - New highs vs new lows
   - **Recommendation**: Add to Leading Indicators

3. **Corporate Credit Stress** ❌
   - High yield spreads (distinct from EM spreads)
   - Investment grade spread widening
   - **Recommendation**: Add to Liquidity Plumbing

4. **Regional Bank Stress** ⚠️
   - 2023 SVB/First Republic showed this gap
   - KRE in original FRS, but need explicit banking indicator
   - **Recommendation**: Add bank deposit flows or FDIC problem bank count

5. **Developed Market Stress** ❌
   - Focus on EM, but DM issues also spread (2022 UK gilt crisis)
   - **Recommendation**: Add DM stress indicator to Global Contagion

6. **Income Distribution** ❌
   - Consumer stress uses averages, not distribution
   - Subprime vs prime consumer divergence
   - **Recommendation**: Add distributional consumer analysis

---

## 🚨 Risk Assessment

### Technical Risks
- **HIGH**: API dependency (FRED API down → EWS fails)
  - *Mitigation*: Robust caching, stale data fallback, manual override capability
- **MEDIUM**: Data quality (revisions, missing data, Yahoo Finance unreliability)
  - *Mitigation*: Data validation, outlier detection, cross-reference multiple sources
- **LOW-MEDIUM**: Calculation errors (complex formulas)
  - *Mitigation*: Comprehensive unit tests, manual validation against historical events

### Methodological Risks
- **HIGH**: Regime change (thresholds based on 2000-2024 may not work in new era)
  - *Mitigation*: Regular threshold recalibration, regime-dependent thresholds
- **MEDIUM**: Correlation breakdown (historical relationships may decouple)
  - *Mitigation*: Monitor indicator correlations, flag relationship breakdowns
- **MEDIUM-HIGH**: False signals (leading indicators can give false positives)
  - *Mitigation*: Communicate false positive rates, require multiple confirming signals

### Operational Risks
- **HIGH**: User misinterpretation (retail investors may overreact)
  - *Mitigation*: Clear education, emphasize probabilistic nature, graduated actions
- **MEDIUM**: Overfitting (13 indicators with specific thresholds may not generalize)
  - *Mitigation*: Out-of-sample testing, simplicity bias, regular effectiveness review
- **LOW-MEDIUM**: Maintenance burden (13 indicators to monitor)
  - *Mitigation*: Automated monitoring, clear documentation, prioritize critical indicators

---

## ✅ Prioritized Recommendations

### 🔴 MUST-HAVE (P0) - Block deployment without these

1. **Reconsider VP weighting**
   - Change from: `0.65 FRS / 0.20 EWS / 0.15 VP`
   - To: `0.60 FRS / 0.20 EWS / 0.20 VP`
   - Justification: Preserve tactical warning capability

2. **Add systematic backtesting**
   - Test 2007-2008, 2018 Q4, 2020, 2022 events
   - Show lead times and false positives
   - Validate new formula outperforms current CMDS

3. **Replace MOVE Index dependency**
   - Use FRED alternatives: `BAMLH0A0HYM2`, `T10Y3M`, `TEDRATE`
   - Create Treasury stress composite from multiple FRED series

4. **Add production-grade code quality**
   - Error handling (try/except blocks)
   - Input validation (assertions, type checks)
   - Logging (structured logging for debugging)
   - Type hints (proper function signatures)

5. **Define caching TTL**
   - Daily: 24-hour, Weekly: 7-day, Monthly: 30-day, Quarterly: 90-day

6. **Add API versioning strategy**
   - `/api/cmds` (current formula - backward compatible)
   - `/api/cmds?version=2` (new formula)
   - Migration plan for existing users

---

### 🟡 SHOULD-HAVE (P1) - Significantly improves robustness

7. **Data freshness monitoring section**
   - Detection logic for stale data
   - Alerting thresholds

8. **Update schedule table**
   - When each indicator releases
   - Expected update windows
   - Release delays

9. **Threshold calibration methodology**
   - Historical distribution analysis
   - Justification for each threshold
   - Review and recalibration policy

10. **Sensitivity analysis**
    - Test threshold variations ±20%
    - Show impact on historical EWS

11. **False positive analysis**
    - Document known false signal scenarios
    - 2015-2016 dollar strength example

12. **Migration strategy**
    - Parallel run period (6 months)
    - Divergence analysis
    - User education plan

13. **Code standardization**
    - Consistent docstrings
    - Uniform formatting (f-strings)
    - Extract hardcoded values to config

---

### 🟢 NICE-TO-HAVE (P2) - Enhances usability

14. Table of contents with hyperlinks
15. Troubleshooting section
16. Glossary of technical terms
17. UI/UX recommendations
18. Correlation analysis (EWS categories)
19. Crisis typology section
20. Interaction effects between categories

---

## 📋 Implementation Roadmap

### Phase 1: Implementation (Months 1-2)
- Implement all 4 EWS categories as modules
- Integrate with existing FRS architecture
- Add error handling, validation, logging (P0 items)
- Replace MOVE Index with FRED alternatives

**Deliverables**:
- `backend/analytics/core/categories/global_contagion.py`
- `backend/analytics/core/categories/leading_indicators.py`
- `backend/analytics/core/categories/liquidity_plumbing.py`
- `backend/analytics/core/categories/consumer_stress.py`
- `backend/analytics/core/ews_calculator.py`
- Unit tests for all categories
- Integration with `frs_calculator.py`

### Phase 2: Validation (Months 3-4)
- Backtest on historical data (2007-2024)
- Run new CMDS in parallel with current formula
- Analyze divergences and validate improvements
- Refine thresholds based on findings

**Deliverables**:
- Historical backtesting report
- Sensitivity analysis results
- False positive analysis
- Threshold refinement recommendations

### Phase 3: Refinement (Months 5-6)
- Add operational monitoring (data freshness, alerting)
- Implement UI/UX for EWS display
- User education materials
- Documentation finalization

**Deliverables**:
- Data freshness monitoring system
- Alert notification system
- Frontend components for EWS display
- User guide and educational content

### Phase 4: Deployment (Month 7)
- Soft launch with beta users
- Gather feedback and iterate
- Full production deployment
- Monitor performance and user adoption

**Deliverables**:
- Beta user feedback report
- Production deployment
- Performance monitoring dashboard
- User adoption metrics

---

## 📊 Dimension Scores Summary

| Dimension | Score | Status | Key Issue |
|-----------|-------|--------|-----------|
| Technical Accuracy | 8/10 | ✅ Good | Threshold justification needed |
| CMDS Formula | 6/10 | ⚠️ Needs work | VP weight too low |
| Data Source Reliability | 7/10 | ✅ Good | MOVE Index concern |
| Implementation Feasibility | 8/10 | ✅ Good | Missing caching specs |
| Code Quality | 7/10 | ✅ Good | No error handling |
| Methodology Soundness | 7/10 | ✅ Good | Inconsistent lookbacks |
| Blind Spots Coverage | 6/10 | ⚠️ Needs work | Missing derivatives stress |
| Integration Strategy | 7/10 | ✅ Good | Need migration plan |
| Historical Validation | 5/10 | ⚠️ Needs work | No backtesting |
| Documentation Quality | 8/10 | ✅ Good | Missing TOC |
| Operational Readiness | 4/10 | ❌ Critical gap | No monitoring |
| User Experience | 6/10 | ⚠️ Needs work | Cognitive load |
| Risk Management | 5/10 | ⚠️ Needs work | High methodology risk |

**Overall**: 7.2/10

---

## 🎯 Final Verdict

**APPROVE WITH CRITICAL MODIFICATIONS**

This specification represents a significant improvement to the FRS framework by adding genuine early warning capabilities. The focus on leading indicators (ISM, jobless claims, housing) addresses a real blind spot in the current system.

**However**, the document is implementation-focused but operationally incomplete. The proposed VP weight reduction is too aggressive, and the lack of systematic backtesting is a major gap.

### Implementation Status

With the **P0 (Must-Have) changes**, this specification is ready for implementation.
With **P1 (Should-Have) changes**, it becomes production-robust.
**P2 (Nice-to-Have) changes** make it comprehensive and user-friendly.

### Estimated Effort

- **P0 changes**: 2-3 weeks
- **Full implementation with P0+P1**: 6-8 weeks of development
- **Validation period**: 2-3 months of parallel running
- **Total time to production**: ~5-6 months

### Key Success Metrics

1. **Early warning accuracy**: EWS provides 3-12 month lead time on major corrections
2. **False positive rate**: <30% (acceptable for early warning system)
3. **User adoption**: >70% of users find EWS actionable
4. **System reliability**: >99% uptime, <500ms API response time
5. **Data freshness**: >95% of indicators updated within expected windows

### Next Steps

1. **Immediate**: Review P0 recommendations with stakeholders
2. **Week 1**: Decision on VP weighting (0.15 vs 0.20)
3. **Week 2-3**: Begin historical backtesting analysis
4. **Week 4**: Finalize specification with P0 changes
5. **Month 2**: Begin Phase 1 implementation

---

**The phased rollout approach minimizes risk while maximizing learning from real-world data. This is the right path forward for enhancing TradeEdge's risk detection capabilities.**

---

## 📚 Appendix: Quick Reference

### FRED Series Used
- `DTWEXBGS` - Dollar Index (Daily)
- `BAMLEMCBPIOAS` - EM Credit Spreads (Daily)
- `NAPMNOI` - ISM New Orders (Monthly)
- `NAPMII` - ISM Inventories (Monthly)
- `ICSA` - Initial Claims (Weekly)
- `PERMIT` - Housing Permits (Monthly)
- `NFCI` - Chicago Fed Financial Conditions (Weekly)
- `WALCL` - Fed Balance Sheet (Weekly)
- `DRCCLACBS` - Credit Card Delinquency (Quarterly)
- `DRALACBS` - Consumer Loan Delinquency (Quarterly)
- `PSAVERT` - Personal Savings Rate (Monthly)

### Proposed FRED Alternatives for MOVE Index
- `BAMLH0A0HYM2` - High Yield spread
- `T10Y3M` - 10Y-3M Treasury spread
- `TEDRATE` - TED spread

### EWS Category Structure
```
Early Warning Score (0-40 points)
├── Global Contagion (0-10)
│   ├── Dollar Strength (0-5)
│   └── EM Stress (0-5)
├── Leading Indicators (0-10)
│   ├── ISM Gap (0-4)
│   ├── Jobless Claims Trend (0-3)
│   └── Housing Permits (0-3)
├── Liquidity Plumbing (0-10)
│   ├── Financial Conditions Index (0-4)
│   ├── Treasury Stress (0-3)
│   └── Fed Balance Sheet (0-3)
└── Consumer Stress (0-10)
    ├── Credit Card Delinquency (0-4)
    ├── Auto Loan Delinquency (0-3)
    └── Personal Savings Rate (0-3)
```

### Recommended Caching TTL
| Frequency | TTL | Example Indicators |
|-----------|-----|-------------------|
| Daily | 24 hours | DXY, EM spreads |
| Weekly | 7 days | NFCI, Fed BS, jobless claims |
| Monthly | 30 days | ISM, permits, savings rate |
| Quarterly | 90 days | CC delinquency, auto delinquency |

---

**End of Analysis**

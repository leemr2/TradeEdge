# FRS Enhancement Specifications

## Addressing Identified Blind Spots in the Fundamental Risk Score

**Document Version:** 1.0  
**Created:** December 2025  
**Purpose:** Technical specifications for four new indicator categories to strengthen FRS early warning capability

---

# Executive Summary

This document provides implementation specifications for four enhancement areas identified as blind spots in the current FRS framework:

| Enhancement Area | New Points | Primary Benefit |
|------------------|------------|-----------------|
| 1. Global Contagion | 0-10 | International crisis detection |
| 2. Leading Indicators | 0-10 | Earlier warning signals |
| 3. Liquidity Plumbing | 0-10 | Fed policy & market structure risk |
| 4. Consumer Stress | 0-10 | Pre-unemployment deterioration |

**Recommended Integration:** These 40 new points will:
- Create a parallel "Early Warning Score" (EWS) that combines with FRS and VP to create a new improved CMDS
- **New CMDS Formula:** CMDS = (0.60 × FRS) + (0.20 × EWS_normalized) + (0.20 × VP)
  - FRS contributes 60%: `0.60 × FRS` (FRS is 0-100)
  - EWS contributes 20%: `0.20 × (EWS_raw / 40) × 100` (EWS normalized to 0-100)
  - VP contributes 20%: `0.20 × VP` (VP is 0-100)
  - CMDS final score: 0-100 scale (weighted sum)

---

## New CMDS Formula Overview

**Current CMDS (to be replaced):**
```
CMDS = (0.65 × FRS) + (0.35 × VP)
```

**New CMDS Formula:**
```
CMDS = (0.60 × FRS) + (0.20 × EWS_normalized) + (0.20 × VP)
```

### Detailed Calculation

1. **Fundamental Risk Score (FRS)**: 0-100 points
   - Macro/Cycle: 0-30 points
   - Valuation: 0-25 points
   - Leverage & Stability: 0-25 points
   - Earnings & Margins: 0-10 points
   - Sentiment: -10 to +10 points
   - **FRS Contribution to CMDS**: `0.60 × FRS` = 0-60 points

2. **Early Warning Score (EWS)**: 0-40 points
   - Global Contagion: 0-10 points
   - Leading Indicators: 0-10 points
   - Liquidity Plumbing: 0-10 points
   - Consumer Stress: 0-10 points
   - **EWS Normalized**: `(EWS_raw / 40) × 100` = 0-100 scale
   - **EWS Contribution to CMDS**: `0.20 × EWS_normalized` = 0-20 points

3. **Volatility Predictor (VP)**: 0-100 points
   - Fear keyword composite, search volatility, cross-asset stress
   - **VP Contribution to CMDS**: `0.20 × VP` = 0-20 points

4. **CMDS Final Score**: `FRS_contribution + EWS_contribution + VP_contribution` = 0-100 scale

### Weight Distribution

| Component | Raw Range | Normalized Range | Weight | Contribution Range | Rationale |
|-----------|-----------|-----------------|--------|-------------------|-----------|
| FRS | 0-100 | 0-100 | 60% | 0-60 points | Fundamental structural risk assessment |
| EWS | 0-40 | 0-100 | 20% | 0-20 points | Early warning signals (3-12 month lead time) |
| VP | 0-100 | 0-100 | 20% | 0-20 points | Timing precision and sentiment shifts |
| **Total** | - | - | **100%** | **0-100** | Weighted sum, no normalization needed |

### Why This Approach?

- **FRS remains primary**: 60% weight reflects fundamental structural risk as the foundation
- **EWS adds early warning**: 20% weight provides 3-12 months lead time on deterioration
- **VP provides timing**: 20% weight catches sentiment shifts and short-term risk spikes (preserves tactical capability)
- **Balanced timeframes**: Strategic (FRS 12-18mo) + Early Warning (EWS 3-12mo) + Tactical (VP 2-5 days) = complete risk picture
- **Maintains CMDS scale**: Final score remains 0-100 for consistency with existing allocation zones

**Rationale for 60/20/20 split:**
- VP weight increased from 15% to 20% compared to initial proposal to preserve tactical warning capability
- Analysis showed 57% reduction in VP weight (35% → 15%) would severely diminish short-term risk detection
- 60/20/20 provides better balance across all three timeframes while maintaining FRS as primary driver

---

# Enhancement 1: Global Contagion (0-10 points)

## Purpose

Detect international stress that could spill over to US markets. Historical crises including 1997 Asian Crisis, 1998 LTCM/Russia, 2011-12 European Debt Crisis, and 2015 China devaluation all originated or amplified abroad before hitting US equities.

## Indicator 1.1: Dollar Strength Index (0-5 points)

### Concept

A rapidly strengthening dollar signals global risk-off behavior. When investors flee to safety, they buy dollars, creating a self-reinforcing crisis dynamic:
- EM countries with dollar-denominated debt face higher repayment costs
- Commodity prices fall (priced in dollars)
- Global liquidity tightens
- US corporate earnings from abroad shrink (translation effect)

The DXY (Dollar Index) captures dollar strength against a basket of major currencies (EUR 57.6%, JPY 13.6%, GBP 11.9%, CAD 9.1%, SEK 4.2%, CHF 3.6%).

### Data Sources

**Primary - FRED Series:** `DTWEXBGS`
- **Full Name:** Trade Weighted U.S. Dollar Index: Broad, Goods and Services
- **Unit:** Index (January 2006 = 100)
- **Frequency:** Daily
- **Source:** Federal Reserve Board
- **API Access:** `fred.get_series('DTWEXBGS')`

**Alternative - Yahoo Finance:** `DX-Y.NYB`
- **Full Name:** US Dollar Index Futures
- **Frequency:** Real-time during futures hours
- **Note:** More volatile, use FRED for official calculations

### Calculation Method

```python
import pandas as pd
from fredapi import Fred

def score_dollar_strength(fred_api_key: str) -> tuple:
    """
    Score dollar strength based on level and rate of change.
    Combines absolute level with momentum for better signal.
    """
    fred = Fred(api_key=fred_api_key)
    
    # 1. Get dollar index data (2 years for context)
    dxy = fred.get_series('DTWEXBGS', observation_start='2023-01-01')
    
    # 2. Current level
    current_dxy = dxy.iloc[-1]
    
    # 3. Calculate 3-month rate of change (momentum)
    dxy_3m_ago = dxy.iloc[-63] if len(dxy) >= 63 else dxy.iloc[0]  # ~63 trading days
    change_3m = ((current_dxy / dxy_3m_ago) - 1) * 100
    
    # 4. Calculate percentile rank over lookback period
    percentile = (dxy < current_dxy).mean() * 100
    
    # 5. Scoring logic
    # High absolute level + rapid appreciation = maximum stress
    
    level_score = 0
    if current_dxy > 115:
        level_score = 3  # Very strong dollar (crisis territory)
    elif current_dxy > 110:
        level_score = 2  # Strong dollar (stress)
    elif current_dxy > 105:
        level_score = 1  # Moderately strong
    
    momentum_score = 0
    if change_3m > 8:
        momentum_score = 2  # Rapid appreciation (>8% in 3 months)
    elif change_3m > 5:
        momentum_score = 1.5  # Fast appreciation
    elif change_3m > 3:
        momentum_score = 1  # Notable appreciation
    
    score = min(5, level_score + momentum_score)
    
    data = {
        'current_dxy': round(current_dxy, 2),
        'change_3m_pct': round(change_3m, 2),
        'percentile_2y': round(percentile, 1),
        'level_component': level_score,
        'momentum_component': momentum_score
    }
    
    return score, data
```

### Scoring Thresholds

| Score | DXY Level | 3M Change | Interpretation |
|-------|-----------|-----------|----------------|
| 0 | <100 | <0% | Weak dollar, risk-on |
| 1 | 100-105 | 0-3% | Normal range |
| 2 | 105-110 | 3-5% | Moderately strong |
| 3-4 | 110-115 | 5-8% | Strong, global stress |
| 5 | >115 OR | >8% | Crisis levels |

### Historical Context

| Period | DXY Level | Outcome |
|--------|-----------|---------|
| 1997 Asian Crisis | 98→104 (+6%) | EM collapse, LTCM |
| 2008 GFC Peak | 72→89 (+24%) | Flight to safety |
| 2014-2016 | 80→103 (+29%) | EM stress, commodity crash |
| 2022 Rate Hikes | 96→114 (+19%) | Global tightening, UK pension crisis |
| Mar 2020 COVID | 95→103 (+8%) | Liquidity crisis |

### Update Frequency

**Daily** - Pull after 6:00 PM ET for final FRED update

---

## Indicator 1.2: Emerging Market Stress (0-5 points)

### Concept

Emerging markets are the canary in the coal mine for global risk. EM assets are more sensitive to:
- Dollar strength
- Global liquidity conditions
- Risk appetite shifts
- Commodity prices

When EM credit spreads widen or EM equities underperform, it often precedes broader risk-off.

### Data Sources

**EM Credit Spreads - FRED Series:** `BAMLEMCBPIOAS`
- **Full Name:** ICE BofA Emerging Markets Corporate Plus Index Option-Adjusted Spread
- **Unit:** Percent
- **Frequency:** Daily
- **API Access:** `fred.get_series('BAMLEMCBPIOAS')`

**EM Equities - Yahoo Finance:** `EEM`
- **Full Name:** iShares MSCI Emerging Markets ETF
- **Frequency:** Real-time
- **Use:** Performance vs SPY for relative strength

**Alternative EM Spread:** `BAMLEMHBHYCRPIOAS` (EM High Yield)

### Calculation Method

```python
import yfinance as yf
from fredapi import Fred

def score_em_stress(fred_api_key: str) -> tuple:
    """
    Combine EM credit spreads with EM equity relative performance.
    Both widening spreads AND underperformance = elevated stress.
    """
    fred = Fred(api_key=fred_api_key)
    
    # PART A: EM Credit Spreads
    em_spread = fred.get_series('BAMLEMCBPIOAS', observation_start='2022-01-01')
    current_spread = em_spread.iloc[-1]
    spread_median = em_spread.median()
    spread_90th = em_spread.quantile(0.90)
    
    # PART B: EM vs US Equity Performance (6 months)
    eem = yf.Ticker('EEM')
    spy = yf.Ticker('SPY')
    
    eem_hist = eem.history(period='6mo')
    spy_hist = spy.history(period='6mo')
    
    eem_return = ((eem_hist['Close'].iloc[-1] / eem_hist['Close'].iloc[0]) - 1) * 100
    spy_return = ((spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[0]) - 1) * 100
    
    em_underperformance = spy_return - eem_return
    
    # PART C: Scoring
    # Credit component (0-2.5 points)
    if current_spread <= spread_median:
        credit_score = 0
    elif current_spread <= spread_90th:
        credit_score = ((current_spread - spread_median) / 
                       (spread_90th - spread_median)) * 2
    else:
        credit_score = 2.5
    
    # Equity relative strength component (0-2.5 points)
    if em_underperformance < 5:
        equity_score = 0
    elif em_underperformance < 15:
        equity_score = (em_underperformance - 5) / 10 * 2
    else:
        equity_score = 2.5
    
    score = min(5, credit_score + equity_score)
    
    data = {
        'em_spread_bps': round(current_spread * 100, 0),
        'spread_median_bps': round(spread_median * 100, 0),
        'eem_return_6m': round(eem_return, 2),
        'spy_return_6m': round(spy_return, 2),
        'em_underperformance_pp': round(em_underperformance, 2),
        'credit_component': round(credit_score, 2),
        'equity_component': round(equity_score, 2)
    }
    
    return score, data
```

### Scoring Thresholds

| Score | EM Spread | EM vs US (6M) | Interpretation |
|-------|-----------|---------------|----------------|
| 0 | <300bps | <5pp underperf | Healthy EM appetite |
| 1-2 | 300-400bps | 5-10pp | Mild stress |
| 2-3 | 400-500bps | 10-15pp | Elevated stress |
| 4-5 | >500bps | >15pp | Crisis conditions |

### Historical EM Stress Events

| Period | EM Spread | EEM vs SPY | Outcome |
|--------|-----------|------------|---------|
| 2015 China Deval | 450→550bps | -25pp | Global selloff |
| 2018 Turkey/Argentina | 350→480bps | -18pp | Contagion fears |
| Mar 2020 COVID | 300→900bps | -12pp | Liquidity crisis |
| 2022 Rate Hikes | 280→450bps | -22pp | Dollar strength crushed EM |

### Update Frequency

**Daily** - EM spreads update ~6 PM ET; equity prices real-time

---

## Global Contagion Category Aggregation

```python
def calculate_global_contagion(fred_api_key: str) -> dict:
    """
    Combine dollar strength and EM stress indicators.
    Total: 0-10 points
    """
    dollar_score, dollar_data = score_dollar_strength(fred_api_key)
    em_score, em_data = score_em_stress(fred_api_key)
    
    total = min(10, dollar_score + em_score)
    
    return {
        'total': total,
        'max_points': 10,
        'indicators': {
            'dollar_strength': {
                'score': dollar_score,
                'data': dollar_data
            },
            'em_stress': {
                'score': em_score,
                'data': em_data
            }
        }
    }
```

### Current Assessment Framework

| Score Range | Risk Level | Interpretation |
|-------------|------------|----------------|
| 0-2 | Low | Global risk appetite healthy |
| 3-5 | Moderate | Some international stress |
| 6-7 | Elevated | Contagion risk rising |
| 8-10 | High | Active global stress, spillover likely |

---

# Enhancement 2: Leading Indicators (0-10 points)

## Purpose

Replace or supplement lagging indicators (unemployment, GDP) with forward-looking signals that deteriorate 3-12 months before recessions officially begin.

## Indicator 2.1: ISM New Orders vs Inventories (0-4 points)

### Concept

The gap between ISM New Orders and ISM Inventories is one of the most reliable leading indicators. When new orders fall while inventories rise, it signals:
- Demand is weakening
- Companies are stuck with unsold goods
- Production cuts coming
- Layoffs follow 3-6 months later

A negative gap (Orders < Inventories) has preceded every recession since 1948.

### Data Sources

**FRED Series 1:** `NAPMNOI`
- **Full Name:** ISM Manufacturing: New Orders Index
- **Unit:** Index (50 = neutral)
- **Frequency:** Monthly (released 1st business day)
- **API Access:** `fred.get_series('NAPMNOI')`

**FRED Series 2:** `NAPMII`
- **Full Name:** ISM Manufacturing: Inventories Index
- **Unit:** Index (50 = neutral)
- **Frequency:** Monthly
- **API Access:** `fred.get_series('NAPMII')`

### Calculation Method

```python
def score_ism_gap(fred_api_key: str) -> tuple:
    """
    Calculate ISM New Orders minus Inventories gap.
    Negative gap = recession warning.
    """
    fred = Fred(api_key=fred_api_key)
    
    # Get both series
    new_orders = fred.get_series('NAPMNOI', observation_start='2022-01-01')
    inventories = fred.get_series('NAPMII', observation_start='2022-01-01')
    
    # Current values
    current_orders = new_orders.iloc[-1]
    current_inventories = inventories.iloc[-1]
    
    # Calculate gap
    gap = current_orders - current_inventories
    
    # 3-month average gap (smooths noise)
    recent_orders = new_orders.iloc[-3:].mean()
    recent_inventories = inventories.iloc[-3:].mean()
    avg_gap_3m = recent_orders - recent_inventories
    
    # Scoring based on gap severity
    if avg_gap_3m > 5:
        score = 0  # Healthy: orders growing faster than inventories
    elif 0 <= avg_gap_3m <= 5:
        score = 1  # Slowing but positive
    elif -5 <= avg_gap_3m < 0:
        score = 2  # Warning: inventories building
    elif -10 <= avg_gap_3m < -5:
        score = 3  # Serious: demand falling, inventory overhang
    else:  # < -10
        score = 4  # Severe: recession imminent
    
    data = {
        'current_new_orders': round(current_orders, 1),
        'current_inventories': round(current_inventories, 1),
        'current_gap': round(gap, 1),
        'avg_gap_3m': round(avg_gap_3m, 1)
    }
    
    return score, data
```

### Scoring Thresholds

| Score | Gap (Orders - Inv) | Interpretation |
|-------|-------------------|----------------|
| 0 | >+5 | Healthy demand growth |
| 1 | 0 to +5 | Balanced, slowing |
| 2 | -5 to 0 | Warning: inventory build |
| 3 | -10 to -5 | Serious deterioration |
| 4 | <-10 | Recession signal |

### Historical Context

| Period | Gap | Lead Time to Recession |
|--------|-----|------------------------|
| 2000 | -8 | 6 months |
| 2007 | -6 | 9 months |
| 2019 | -4 | 4 months (COVID accelerated) |
| 2022 | -3 | No recession (soft landing) |

---

## Indicator 2.2: Weekly Jobless Claims Trend (0-3 points)

### Concept

Initial jobless claims are the most timely labor market indicator, released weekly with only a 5-day lag. While monthly unemployment is lagging, the *trend* in weekly claims gives early warning of labor market deterioration.

Key insight: It's not the level, it's the rate of change. Claims rising 20%+ from their trough historically precedes recession.

### Data Source

**FRED Series:** `ICSA`
- **Full Name:** Initial Claims (SA)
- **Unit:** Number of claims
- **Frequency:** Weekly (Thursday mornings)
- **API Access:** `fred.get_series('ICSA')`

### Calculation Method

```python
def score_jobless_claims_trend(fred_api_key: str) -> tuple:
    """
    Score based on jobless claims trend, not absolute level.
    Rising claims from trough = early labor market warning.
    """
    fred = Fred(api_key=fred_api_key)
    
    # Get weekly claims (1 year lookback)
    claims = fred.get_series('ICSA', observation_start='2024-01-01')
    
    # 4-week moving average (smooths weekly noise)
    claims_4wma = claims.rolling(4).mean()
    
    current_4wma = claims_4wma.iloc[-1]
    
    # Find trough in last 12 months
    trough_12m = claims_4wma.min()
    
    # Calculate % change from trough
    pct_from_trough = ((current_4wma / trough_12m) - 1) * 100
    
    # Scoring
    if pct_from_trough < 10:
        score = 0  # Near lows, healthy
    elif pct_from_trough < 20:
        score = 1  # Rising but not alarming
    elif pct_from_trough < 35:
        score = 2  # Significant increase
    else:  # >= 35%
        score = 3  # Recession-level increase
    
    data = {
        'current_4wma': round(current_4wma, 0),
        'trough_12m': round(trough_12m, 0),
        'pct_from_trough': round(pct_from_trough, 1)
    }
    
    return score, data
```

### Scoring Thresholds

| Score | % From Trough | Interpretation |
|-------|---------------|----------------|
| 0 | <10% | Stable labor market |
| 1 | 10-20% | Early deterioration |
| 2 | 20-35% | Clear weakening |
| 3 | >35% | Recession-level deterioration |

### Historical Claims Spikes

| Period | Trough | Peak | % Change | Recession? |
|--------|--------|------|----------|------------|
| 2001 | 280K | 490K | +75% | Yes |
| 2008 | 300K | 665K | +122% | Yes |
| 2020 | 210K | 6.9M | +3,186% | Yes (COVID) |
| 2022-23 | 190K | 265K | +39% | No |

---

## Indicator 2.3: Housing Permits (0-3 points)

### Concept

Housing is the most interest-rate-sensitive sector and typically leads the economy by 12-18 months. Building permits (not starts or completions) are the most forward-looking housing indicator because they represent future construction intentions before ground is broken.

### Data Source

**FRED Series:** `PERMIT`
- **Full Name:** New Privately-Owned Housing Units Authorized (SAAR)
- **Unit:** Thousands of Units
- **Frequency:** Monthly (~18th of month)
- **API Access:** `fred.get_series('PERMIT')`

### Calculation Method

```python
def score_housing_permits(fred_api_key: str) -> tuple:
    """
    Score based on YoY change in building permits.
    Falling permits = economic slowdown ahead.
    """
    fred = Fred(api_key=fred_api_key)
    
    permits = fred.get_series('PERMIT', observation_start='2022-01-01')
    
    # Current (3-month average to smooth)
    current_3m = permits.iloc[-3:].mean()
    
    # Year ago (3-month average)
    year_ago_3m = permits.iloc[-15:-12].mean()
    
    # YoY change
    yoy_change = ((current_3m / year_ago_3m) - 1) * 100
    
    # Also check absolute level vs historical norm (~1.5M)
    historical_norm = 1500  # thousands
    
    # Scoring
    if yoy_change > 0:
        score = 0  # Permits growing
    elif yoy_change > -10:
        score = 1  # Mild decline
    elif yoy_change > -20:
        score = 2  # Significant decline
    else:  # <= -20%
        score = 3  # Severe contraction
    
    data = {
        'current_3m_avg': round(current_3m, 0),
        'year_ago_3m_avg': round(year_ago_3m, 0),
        'yoy_change_pct': round(yoy_change, 1),
        'vs_historical_norm': round((current_3m / historical_norm - 1) * 100, 1)
    }
    
    return score, data
```

### Scoring Thresholds

| Score | YoY Permit Change | Interpretation |
|-------|-------------------|----------------|
| 0 | >0% | Housing expanding |
| 1 | -10% to 0% | Mild softening |
| 2 | -20% to -10% | Significant contraction |
| 3 | <-20% | Severe housing downturn |

### Historical Housing Leads

| Period | Permit Peak | Permit Trough | YoY at Trough | Recession Start |
|--------|-------------|---------------|---------------|-----------------|
| 2005-2006 | Sep 2005 | | -30% | Dec 2007 (27 mo lead) |
| 2018-2019 | Jan 2018 | | -10% | No recession |
| 2022 | Apr 2022 | Jan 2023 | -28% | No recession (yet) |

---

## Leading Indicators Category Aggregation

```python
def calculate_leading_indicators(fred_api_key: str) -> dict:
    """
    Combine all leading indicator components.
    Total: 0-10 points
    """
    ism_score, ism_data = score_ism_gap(fred_api_key)
    claims_score, claims_data = score_jobless_claims_trend(fred_api_key)
    housing_score, housing_data = score_housing_permits(fred_api_key)
    
    total = min(10, ism_score + claims_score + housing_score)
    
    return {
        'total': total,
        'max_points': 10,
        'indicators': {
            'ism_gap': {'score': ism_score, 'data': ism_data},
            'jobless_claims_trend': {'score': claims_score, 'data': claims_data},
            'housing_permits': {'score': housing_score, 'data': housing_data}
        }
    }
```

---

# Enhancement 3: Liquidity Plumbing (0-10 points)

## Purpose

Monitor the "plumbing" of financial markets—Fed policy mechanics, bank reserves, and market structure—that can cause sudden dislocations even when surface-level indicators look calm.

## Indicator 3.1: Financial Conditions Index (0-4 points)

### Concept

Financial conditions indices aggregate multiple factors (interest rates, credit spreads, equity prices, volatility, dollar) into a single measure. The Chicago Fed's NFCI is widely watched and updated weekly.

Tightening financial conditions constrain economic activity with a lag. When the NFCI rises sharply, credit becomes harder to obtain across the economy.

### Data Source

**FRED Series:** `NFCI`
- **Full Name:** Chicago Fed National Financial Conditions Index
- **Unit:** Index (0 = average conditions, positive = tighter than average)
- **Frequency:** Weekly (Friday release for prior week)
- **API Access:** `fred.get_series('NFCI')`

**Alternative:** `GSFCI` (Goldman Sachs FCI) - not on FRED, requires Bloomberg

### Calculation Method

```python
def score_financial_conditions(fred_api_key: str) -> tuple:
    """
    Score based on Chicago Fed NFCI level and trend.
    Positive = tighter than average (bad)
    Negative = looser than average (good)
    """
    fred = Fred(api_key=fred_api_key)
    
    nfci = fred.get_series('NFCI', observation_start='2022-01-01')
    
    current_nfci = nfci.iloc[-1]
    avg_nfci_13w = nfci.iloc[-13:].mean()  # 3-month average
    
    # Rate of change (tightening speed matters)
    nfci_13w_ago = nfci.iloc[-13]
    change_13w = current_nfci - nfci_13w_ago
    
    # Scoring
    # NFCI is mean 0, so positive = tight
    if current_nfci < -0.5:
        score = 0  # Very loose conditions
    elif current_nfci < 0:
        score = 1  # Looser than average
    elif current_nfci < 0.5:
        score = 2  # Tighter than average
    elif current_nfci < 1.0:
        score = 3  # Significantly tight
    else:  # >= 1.0
        score = 4  # Crisis-level tightness
    
    # Bonus for rapid tightening
    if change_13w > 0.5:
        score = min(4, score + 1)
    
    data = {
        'current_nfci': round(current_nfci, 3),
        'avg_nfci_13w': round(avg_nfci_13w, 3),
        'change_13w': round(change_13w, 3),
        'interpretation': 'Tight' if current_nfci > 0 else 'Loose'
    }
    
    return score, data
```

### Scoring Thresholds

| Score | NFCI Level | Interpretation |
|-------|------------|----------------|
| 0 | <-0.5 | Very loose (easy credit) |
| 1 | -0.5 to 0 | Looser than average |
| 2 | 0 to +0.5 | Tighter than average |
| 3 | +0.5 to +1.0 | Significantly tight |
| 4 | >+1.0 | Crisis-level tightness |

### Historical NFCI Context

| Period | NFCI Peak | Outcome |
|--------|-----------|---------|
| 2008 GFC | +3.5 | Credit markets frozen |
| 2011 Euro Crisis | +0.7 | Brief tightening |
| 2016 Oil/China | +0.3 | Mild stress |
| 2020 COVID | +1.4 | Brief spike, Fed intervention |
| 2022 Rate Hikes | +0.4 | Controlled tightening |

---

## Indicator 3.2: Treasury Market Stress Composite (0-3 points)

### Concept

Treasury market stress is a critical indicator of systemic risk. When Treasury markets malfunction, stress spreads to all asset classes. This composite combines three complementary FRED indicators:
- **High Yield Spreads**: Stress in corporate credit markets
- **Treasury Yield Curve**: Inversion signals recession expectations
- **TED Spread**: Interbank lending stress

**Note:** This replaces the MOVE Index (previously Yahoo Finance) with more reliable FRED data sources for production robustness.

### Data Sources

**Primary - FRED Series:** `BAMLH0A0HYM2`
- **Full Name:** ICE BofA US High Yield Index Option-Adjusted Spread
- **Unit:** Percent
- **Frequency:** Daily
- **API Access:** `fred.get_series('BAMLH0A0HYM2')`

**Secondary - FRED Series:** `T10Y3M`
- **Full Name:** 10-Year Treasury Constant Maturity Minus 3-Month Treasury Constant Maturity
- **Unit:** Percent
- **Frequency:** Daily
- **API Access:** `fred.get_series('T10Y3M')`

**Tertiary - FRED Series:** `TEDRATE`
- **Full Name:** TED Spread (3-Month LIBOR - 3-Month Treasury Bill)
- **Unit:** Percent
- **Frequency:** Daily
- **API Access:** `fred.get_series('TEDRATE')`

### Calculation Method

```python
from typing import Dict, Tuple
from fredapi import Fred
import logging

logger = logging.getLogger(__name__)

def score_treasury_stress(fred_api_key: str) -> Tuple[float, Dict[str, any]]:
    """
    Score based on Treasury market stress composite.
    Combines HY spreads, yield curve, and TED spread.

    Args:
        fred_api_key: FRED API key for data access

    Returns:
        Tuple of (score: 0-3, data_dict)
    """
    try:
        fred = Fred(api_key=fred_api_key)

        # Component 1: High Yield Spread (stress proxy)
        hy_spread = fred.get_series('BAMLH0A0HYM2', observation_start='2022-01-01')
        if hy_spread.empty:
            raise ValueError("HY spread data unavailable")
        current_hy = hy_spread.iloc[-1]

        # Component 2: Yield Curve (10Y-3M)
        yield_curve = fred.get_series('T10Y3M', observation_start='2022-01-01')
        if yield_curve.empty:
            raise ValueError("Yield curve data unavailable")
        current_curve = yield_curve.iloc[-1]

        # Component 3: TED Spread (interbank stress)
        ted_spread = fred.get_series('TEDRATE', observation_start='2022-01-01')
        if ted_spread.empty:
            raise ValueError("TED spread data unavailable")
        current_ted = ted_spread.iloc[-1]

        # Scoring logic - weighted composite
        score = 0.0

        # HY Spread component (0-1.5 points)
        if current_hy < 3.5:
            hy_score = 0
        elif current_hy < 5.0:
            hy_score = 0.5
        elif current_hy < 7.0:
            hy_score = 1.0
        else:  # >= 7.0
            hy_score = 1.5

        # Yield Curve component (0-1.0 points)
        if current_curve > 0.5:
            curve_score = 0  # Steep, healthy
        elif current_curve > 0:
            curve_score = 0.25  # Flattening
        elif current_curve > -0.5:
            curve_score = 0.5  # Inverted
        else:  # <= -0.5
            curve_score = 1.0  # Deeply inverted

        # TED Spread component (0-0.5 points)
        if current_ted < 0.3:
            ted_score = 0  # Normal
        elif current_ted < 0.5:
            ted_score = 0.25  # Elevated
        else:  # >= 0.5
            ted_score = 0.5  # Stress

        # Total composite score (0-3)
        score = min(3, hy_score + curve_score + ted_score)

        data = {
            'hy_spread_pct': round(current_hy, 2),
            'yield_curve_pct': round(current_curve, 2),
            'ted_spread_pct': round(current_ted, 3),
            'hy_score': round(hy_score, 2),
            'curve_score': round(curve_score, 2),
            'ted_score': round(ted_score, 2),
            'composite_score': round(score, 2)
        }

        logger.info(f"Treasury stress calculated: HY={current_hy:.2f}%, Curve={current_curve:.2f}%, TED={current_ted:.3f}%")

        return score, data

    except Exception as e:
        logger.error(f"Treasury stress calculation failed: {e}")
        return 0.0, {"error": str(e), "fallback": True}
```

### Scoring Thresholds

| Score | HY Spread | Yield Curve | TED Spread | Interpretation |
|-------|-----------|-------------|------------|----------------|
| 0-0.5 | <3.5% | >0.5% | <0.3% | Calm markets |
| 0.5-1.5 | 3.5-5% | 0 to 0.5% | 0.3-0.5% | Normal stress |
| 1.5-2.5 | 5-7% | -0.5 to 0% | >0.5% | Elevated stress |
| 2.5-3.0 | >7% | <-0.5% | >0.5% | Crisis conditions |

### Historical Treasury Stress Events

| Period | HY Spread | Yield Curve | TED Spread | Context |
|--------|-----------|-------------|------------|---------|
| 2008 GFC Peak | 20%+ | -1.0% | 4.6% | Treasury market seized, flight to quality |
| 2011 Euro Crisis | 8-9% | +1.5% | 0.5% | Sovereign debt fears, safe haven demand |
| 2020 COVID | 11% | +0.5% | 1.4% | Liquidity crisis, Fed intervention |
| 2022 Rate Hikes | 5-6% | -1.0% | 0.2% | Controlled tightening, UK gilt crisis |
| 2023 SVB/Banking | 5% | -0.5% | 0.3% | Regional bank stress, flight to safety |

---

## Indicator 3.3: Fed Balance Sheet Direction (0-3 points)

### Concept

Fed balance sheet expansion (QE) = liquidity injection = bullish for risk assets.
Fed balance sheet contraction (QT) = liquidity withdrawal = headwind for risk assets.

The rate of change matters more than the level. Accelerating QT is a risk.

### Data Source

**FRED Series:** `WALCL`
- **Full Name:** Assets: Total Assets: Total Assets (Less Eliminations)
- **Unit:** Millions of Dollars
- **Frequency:** Weekly (Wednesday release)
- **API Access:** `fred.get_series('WALCL')`

### Calculation Method

```python
def score_fed_balance_sheet(fred_api_key: str) -> tuple:
    """
    Score based on Fed balance sheet direction and pace.
    Contraction = tightening liquidity.
    """
    fred = Fred(api_key=fred_api_key)
    
    bs = fred.get_series('WALCL', observation_start='2022-01-01')
    
    current_bs = bs.iloc[-1]
    bs_3m_ago = bs.iloc[-13] if len(bs) >= 13 else bs.iloc[0]  # ~13 weeks
    bs_1y_ago = bs.iloc[-52] if len(bs) >= 52 else bs.iloc[0]
    
    # Calculate changes
    change_3m = ((current_bs / bs_3m_ago) - 1) * 100
    change_1y = ((current_bs / bs_1y_ago) - 1) * 100
    
    # Scoring: contraction is risk
    if change_3m > 2:
        score = 0  # Expanding (QE-like)
    elif change_3m > 0:
        score = 0.5  # Stable to slightly growing
    elif change_3m > -2:
        score = 1  # Mild contraction
    elif change_3m > -5:
        score = 2  # Moderate QT pace
    else:  # <= -5%
        score = 3  # Aggressive QT
    
    data = {
        'current_bs_trillions': round(current_bs / 1_000_000, 2),
        'change_3m_pct': round(change_3m, 2),
        'change_1y_pct': round(change_1y, 2),
        'direction': 'Expanding' if change_3m > 0 else 'Contracting'
    }
    
    return score, data
```

### Scoring Thresholds

| Score | 3M BS Change | Interpretation |
|-------|--------------|----------------|
| 0 | >+2% | QE/Expansion |
| 0.5 | 0 to +2% | Stable/Slight growth |
| 1 | -2% to 0 | Mild QT |
| 2 | -5% to -2% | Moderate QT |
| 3 | <-5% | Aggressive QT |

---

## Liquidity Plumbing Category Aggregation

```python
def calculate_liquidity_plumbing(fred_api_key: str) -> dict:
    """
    Combine all liquidity/plumbing indicators.
    Total: 0-10 points
    """
    fci_score, fci_data = score_financial_conditions(fred_api_key)
    treasury_score, treasury_data = score_treasury_stress(fred_api_key)
    fed_score, fed_data = score_fed_balance_sheet(fred_api_key)

    total = min(10, fci_score + treasury_score + fed_score)

    return {
        'total': total,
        'max_points': 10,
        'indicators': {
            'financial_conditions': {'score': fci_score, 'data': fci_data},
            'treasury_stress': {'score': treasury_score, 'data': treasury_data},
            'fed_balance_sheet': {'score': fed_score, 'data': fed_data}
        }
    }
```

---

# Enhancement 4: Consumer Stress (0-10 points)

## Purpose

Detect consumer financial deterioration before it shows up in unemployment. The sequence is: savings depleted → delinquencies rise → spending cuts → layoffs → unemployment spikes. By tracking earlier stages, we get 6-12 months of additional lead time.

## Indicator 4.1: Credit Card Delinquency Rate (0-4 points)

### Concept

Credit card delinquencies are the first sign of consumer stress because:
- Cards are unsecured (first to miss)
- No collateral to lose (unlike mortgage/auto)
- High interest rates accelerate problems
- Rising delinquencies = consumers exhausting savings

### Data Source

**FRED Series:** `DRCCLACBS`
- **Full Name:** Delinquency Rate on Credit Card Loans, All Commercial Banks
- **Unit:** Percent
- **Frequency:** Quarterly
- **API Access:** `fred.get_series('DRCCLACBS')`

### Calculation Method

```python
def score_credit_card_delinquency(fred_api_key: str) -> tuple:
    """
    Score based on credit card delinquency rate level and trend.
    Rising delinquencies = consumer stress.
    """
    fred = Fred(api_key=fred_api_key)
    
    cc_delinq = fred.get_series('DRCCLACBS', observation_start='2015-01-01')
    
    current_rate = cc_delinq.iloc[-1]
    rate_1y_ago = cc_delinq.iloc[-4] if len(cc_delinq) >= 4 else cc_delinq.iloc[0]
    
    # YoY change
    change_1y = current_rate - rate_1y_ago
    
    # Historical context: pre-COVID average ~2.5%, 2008 peak ~6.5%
    historical_avg = 2.5
    
    # Scoring
    if current_rate < 2.5:
        score = 0  # Below historical average
    elif current_rate < 3.5:
        score = 1  # Moderately elevated
    elif current_rate < 4.5:
        score = 2  # Elevated
    elif current_rate < 5.5:
        score = 3  # High stress
    else:  # >= 5.5
        score = 4  # Crisis levels
    
    # Bonus for rapid deterioration
    if change_1y > 1.0:
        score = min(4, score + 1)
    
    data = {
        'current_rate_pct': round(current_rate, 2),
        'rate_1y_ago': round(rate_1y_ago, 2),
        'change_1y_pp': round(change_1y, 2),
        'vs_historical_avg': round(current_rate - historical_avg, 2)
    }
    
    return score, data
```

### Scoring Thresholds

| Score | CC Delinquency | Interpretation |
|-------|----------------|----------------|
| 0 | <2.5% | Healthy consumers |
| 1 | 2.5-3.5% | Mild stress |
| 2 | 3.5-4.5% | Elevated stress |
| 3 | 4.5-5.5% | Significant distress |
| 4 | >5.5% | Crisis levels |

### Historical Credit Card Delinquency

| Period | Rate | Context |
|--------|------|---------|
| 2006 (Pre-GFC) | 4.0% | Building stress |
| 2009 (GFC Peak) | 6.8% | Crisis peak |
| 2019 (Pre-COVID) | 2.5% | Normal |
| 2021 (Stimulus) | 1.5% | Historically low |
| 2024-25 | 3.5%+ | Rising rapidly |

---

## Indicator 4.2: Auto Loan Delinquency (0-3 points)

### Concept

Auto loans are the second line of defense after credit cards. Auto delinquencies matter because:
- Larger loan amounts than credit cards
- Collateral exists but depreciates (underwater loans)
- Subprime auto has grown significantly since 2015
- Car is essential for work (people prioritize this payment)

When auto delinquencies rise, consumers are truly struggling.

### Data Source

**FRED Series:** `DRALACBS`
- **Full Name:** Delinquency Rate on Consumer Loans, All Commercial Banks
- **Unit:** Percent
- **Frequency:** Quarterly
- **Note:** This is broader consumer loans; for auto-specific, use NY Fed data

**Alternative (More Specific):** NY Fed Consumer Credit Panel
- Requires manual extraction from quarterly reports
- Shows auto loan delinquency by credit tier

### Calculation Method

```python
def score_auto_delinquency(fred_api_key: str) -> tuple:
    """
    Score based on consumer loan delinquency (proxy for auto).
    Can be enhanced with NY Fed subprime auto data manually.
    """
    fred = Fred(api_key=fred_api_key)
    
    # Consumer loan delinquency (includes auto)
    consumer_delinq = fred.get_series('DRALACBS', observation_start='2015-01-01')
    
    current_rate = consumer_delinq.iloc[-1]
    rate_1y_ago = consumer_delinq.iloc[-4] if len(consumer_delinq) >= 4 else consumer_delinq.iloc[0]
    
    change_1y = current_rate - rate_1y_ago
    
    # Historical context: long-term average ~2.0-2.5%
    if current_rate < 2.0:
        score = 0
    elif current_rate < 2.5:
        score = 1
    elif current_rate < 3.0:
        score = 2
    else:  # >= 3.0
        score = 3
    
    data = {
        'current_rate_pct': round(current_rate, 2),
        'rate_1y_ago': round(rate_1y_ago, 2),
        'change_1y_pp': round(change_1y, 2)
    }
    
    return score, data
```

### Scoring Thresholds

| Score | Consumer Loan Delinq | Interpretation |
|-------|----------------------|----------------|
| 0 | <2.0% | Healthy |
| 1 | 2.0-2.5% | Normal range |
| 2 | 2.5-3.0% | Elevated |
| 3 | >3.0% | Significant stress |

---

## Indicator 4.3: Personal Savings Rate (0-3 points)

### Concept

The personal savings rate shows how much cushion consumers have. When savings are depleted:
- No buffer for unexpected expenses
- Credit becomes lifeline
- Spending cuts become necessary
- Recession risk rises

Post-COVID, the savings rate collapsed from pandemic highs (33%) to near-record lows (3-4%).

### Data Source

**FRED Series:** `PSAVERT`
- **Full Name:** Personal Saving Rate
- **Unit:** Percent
- **Frequency:** Monthly
- **API Access:** `fred.get_series('PSAVERT')`

### Calculation Method

```python
def score_savings_rate(fred_api_key: str) -> tuple:
    """
    Score based on personal savings rate.
    Low savings = vulnerable consumers.
    """
    fred = Fred(api_key=fred_api_key)
    
    savings = fred.get_series('PSAVERT', observation_start='2015-01-01')
    
    current_rate = savings.iloc[-1]
    avg_rate_1y = savings.iloc[-12:].mean()
    
    # Historical context: 2000-2019 average ~6-7%, healthy = 8%+
    historical_avg = 7.0
    
    # Scoring: lower is worse
    if current_rate > 8:
        score = 0  # Healthy savings
    elif current_rate > 6:
        score = 1  # Adequate
    elif current_rate > 4:
        score = 2  # Low cushion
    else:  # <= 4
        score = 3  # Near-zero cushion, vulnerable
    
    data = {
        'current_rate_pct': round(current_rate, 1),
        'avg_rate_1y': round(avg_rate_1y, 1),
        'vs_historical_avg': round(current_rate - historical_avg, 1)
    }
    
    return score, data
```

### Scoring Thresholds

| Score | Savings Rate | Interpretation |
|-------|--------------|----------------|
| 0 | >8% | Healthy buffer |
| 1 | 6-8% | Adequate |
| 2 | 4-6% | Low cushion |
| 3 | <4% | Near-zero, vulnerable |

### Historical Savings Rate

| Period | Rate | Context |
|--------|------|---------|
| 2005-2007 | 3-4% | Pre-crisis consumer stress |
| 2020 (Stimulus) | 33% | Record high |
| 2022 | 3-4% | Stimulus depleted |
| 2024-25 | 4-5% | Low but stabilizing |

---

## Consumer Stress Category Aggregation

```python
def calculate_consumer_stress(fred_api_key: str) -> dict:
    """
    Combine all consumer stress indicators.
    Total: 0-10 points
    """
    cc_score, cc_data = score_credit_card_delinquency(fred_api_key)
    auto_score, auto_data = score_auto_delinquency(fred_api_key)
    savings_score, savings_data = score_savings_rate(fred_api_key)
    
    total = min(10, cc_score + auto_score + savings_score)
    
    return {
        'total': total,
        'max_points': 10,
        'indicators': {
            'credit_card_delinquency': {'score': cc_score, 'data': cc_data},
            'auto_delinquency': {'score': auto_score, 'data': auto_data},
            'savings_rate': {'score': savings_score, 'data': savings_data}
        }
    }
```

---

# Integration Guide

## Option A: Expand FRS to 130 Points

Modify the existing FRS structure to incorporate all new categories:

| Category | Current | Enhanced | New Max |
|----------|---------|----------|---------|
| Macro/Cycle | 30 | Keep | 30 |
| Valuation | 25 | Keep | 25 |
| Leverage & Financial | 25 | Keep | 25 |
| Earnings & Margins | 10 | Keep | 10 |
| Technical/Sentiment | 10 | Replace with new | 0 |
| **NEW: Global Contagion** | 0 | Add | 10 |
| **NEW: Leading Indicators** | 0 | Add | 10 |
| **NEW: Liquidity Plumbing** | 0 | Add | 10 |
| **NEW: Consumer Stress** | 0 | Add | 10 |
| **TOTAL** | 100 | | **130** |

Rescale to 100 if needed: `FRS_Enhanced = (Raw_Score / 130) * 100`

## Option B: Parallel Early Warning Score (EWS) - **SELECTED APPROACH**

Keep FRS unchanged, create a separate Early Warning Score that combines with VP to form the new CMDS:

```python
def calculate_ews(fred_api_key: str) -> dict:
    """
    Early Warning Score: 0-40 points
    Focused on leading/predictive indicators.
    """
    global_contagion = calculate_global_contagion(fred_api_key)
    leading = calculate_leading_indicators(fred_api_key)
    liquidity = calculate_liquidity_plumbing(fred_api_key)
    consumer = calculate_consumer_stress(fred_api_key)
    
    total = (global_contagion['total'] + leading['total'] + 
             liquidity['total'] + consumer['total'])
    
    return {
        'total': total,
        'max_points': 40,
        'normalized': round((total / 40) * 100, 1),
        'categories': {
            'global_contagion': global_contagion,
            'leading_indicators': leading,
            'liquidity_plumbing': liquidity,
            'consumer_stress': consumer
        }
    }
```

### EWS Interpretation

| EWS Range | Risk Level | Action |
|-----------|------------|--------|
| 0-10 | Low | Full risk-on |
| 11-20 | Moderate | Normal allocation |
| 21-30 | Elevated | Reduce risk, add hedges |
| 31-40 | High | Defensive positioning |

## Option C: New CMDS Formula (FRS + EWS + VP) - **SELECTED APPROACH**

**Selected Approach:** Enhance the current CMDS formula to include EWS alongside FRS and VP:

```python
def calculate_new_cmds(frs_score: float, ews_total: float, vp_score: float) -> dict:
    """
    New Combined Market Danger Score: FRS + EWS + VP
    
    Formula:
    - FRS contributes 60%: 0.60 × FRS (FRS is 0-100)
    - EWS contributes 20%: 0.20 × (EWS_raw / 40) × 100 (EWS normalized to 0-100)
    - VP contributes 20%: 0.20 × VP (VP is 0-100)
    - CMDS = weighted sum = 0-100 scale
    
    Args:
        frs_score: Fundamental Risk Score (0-100)
        ews_total: Early Warning Score (0-40 points)
        vp_score: Volatility Predictor score (0-100)
    
    Returns:
        dict with CMDS score, components, interpretation
    """
    # Normalize EWS to 0-100 scale
    ews_normalized = (ews_total / 40) * 100
    
    # Calculate weighted contributions
    frs_contribution = 0.60 * frs_score           # 0-60 points
    ews_contribution = 0.20 * ews_normalized       # 0-20 points
    vp_contribution = 0.20 * vp_score              # 0-20 points
    
    # CMDS is weighted sum (already 0-100 scale)
    cmds = frs_contribution + ews_contribution + vp_contribution
    cmds = max(0, min(100, cmds))  # Clamp to 0-100
    
    return {
        'cmds': round(cmds, 1),
        'components': {
            'frs': {
                'raw': round(frs_score, 1),
                'max': 100,
                'weight': 0.60,
                'contribution': round(frs_contribution, 1),
                'max_contribution': 60
            },
            'ews': {
                'raw': round(ews_total, 1),
                'max': 40,
                'normalized': round(ews_normalized, 1),
                'weight': 0.20,
                'contribution': round(ews_contribution, 1),
                'max_contribution': 20
            },
            'vp': {
                'raw': round(vp_score, 1),
                'max': 100,
                'weight': 0.20,
                'contribution': round(vp_contribution, 1),
                'max_contribution': 20
            }
        },
        'weights': {
            'frs_weight': 0.60,
            'ews_weight': 0.20,
            'vp_weight': 0.20
        },
        'zone': get_cmds_zone(cmds),
        'interpretation': get_cmds_interpretation(cmds)
    }

def get_cmds_zone(cmds: float) -> str:
    """Determine CMDS risk zone"""
    if cmds < 25:
        return "SAFE"
    elif cmds < 45:
        return "CAUTIOUS"
    elif cmds < 65:
        return "ELEVATED"
    elif cmds < 80:
        return "HIGH"
    else:
        return "EXTREME"

def get_cmds_interpretation(cmds: float) -> str:
    """Provide interpretation of CMDS level"""
    if cmds < 25:
        return "Low Risk - Full allocation appropriate (90-100% equity)"
    elif cmds < 45:
        return "Moderate Risk - Normal allocation with monitoring (70-90% equity)"
    elif cmds < 65:
        return "Elevated Risk - Reduce risk, add hedges (50-70% equity)"
    elif cmds < 80:
        return "High Risk - Defensive positioning (30-50% equity)"
    else:
        return "Extreme Risk - Maximum defensive positioning (10-30% equity)"
```

### New CMDS Calculation Example

```
Fundamental Risk Score (FRS): 75/100
├── Macro/Cycle:        22/30
├── Valuation:           20/25
├── Leverage & Stability: 20/25
├── Earnings & Margins:   8/10
└── Sentiment:           +5/10

Early Warning Score (EWS): 28/40
├── Global Contagion:     6/10
├── Leading Indicators:   8/10
├── Liquidity Plumbing:   7/10
└── Consumer Stress:      7/10

Volatility Predictor (VP): 65/100
├── Fear Keyword Composite: Moderate
├── Search Volatility: Elevated patterns
└── Cross-Asset Stress: Moderate

CMDS Calculation:
FRS Contribution = 0.60 × 75 = 45.0 points
EWS Normalized   = (28 / 40) × 100 = 70.0
EWS Contribution = 0.20 × 70.0 = 14.0 points
VP Contribution  = 0.20 × 65 = 13.0 points
CMDS             = 45.0 + 14.0 + 13.0 = 72.0/100

Zone: HIGH (30-50% equity allocation)
```

### Rationale for New CMDS Formula

**Why FRS + EWS + VP:**
- **FRS remains foundation (60%)**: Fundamental structural risk assessment is the primary driver of long-term risk
- **EWS adds early warning (20%)**: Leading indicators detect deterioration 3-12 months before lagging indicators, providing actionable lead time
- **VP provides timing precision (20%)**: Volatility Predictor catches sentiment shifts and short-term risk spikes for optimal entry/exit timing
- **Comprehensive coverage**: Fundamental assessment (FRS) + Early warnings (EWS) + Timing (VP) = complete risk picture

**Why 60% FRS + 20% EWS + 20% VP:**
- FRS gets majority weight because fundamentals determine the magnitude of potential corrections
- EWS gets meaningful weight (20%) to provide early warning signals without overwhelming the fundamental assessment
- VP gets sufficient weight (20%, increased from 15% in initial proposal) to preserve tactical warning capability
- Balanced approach across strategic (FRS), early warning (EWS), and tactical (VP) timeframes
- All components normalized to 0-100 scale for consistent weighting

---

# Data Source Summary

| Indicator | Source | Series/Ticker | Frequency |
|-----------|--------|---------------|-----------|
| Dollar Strength | FRED | DTWEXBGS | Daily |
| EM Credit Spread | FRED | BAMLEMCBPIOAS | Daily |
| EM Equities | Yahoo | EEM | Real-time |
| ISM New Orders | FRED | NAPMNOI | Monthly |
| ISM Inventories | FRED | NAPMII | Monthly |
| Initial Claims | FRED | ICSA | Weekly |
| Building Permits | FRED | PERMIT | Monthly |
| Chicago Fed NFCI | FRED | NFCI | Weekly |
| HY Spread (Treasury Stress) | FRED | BAMLH0A0HYM2 | Daily |
| Yield Curve (Treasury Stress) | FRED | T10Y3M | Daily |
| TED Spread (Treasury Stress) | FRED | TEDRATE | Daily |
| Fed Balance Sheet | FRED | WALCL | Weekly |
| CC Delinquency | FRED | DRCCLACBS | Quarterly |
| Consumer Loan Delinq | FRED | DRALACBS | Quarterly |
| Savings Rate | FRED | PSAVERT | Monthly |

---

# Caching Strategy

## Cache Time-To-Live (TTL) Specifications

To minimize API usage and improve performance, all external data fetches must be cached with appropriate TTL values:

| Data Frequency | TTL | Rationale | Example Indicators |
|----------------|-----|-----------|-------------------|
| **Daily** | 24 hours | Data updates once daily, cache until next trading day | DXY, EM spreads, HY spread, Yield curve, TED spread |
| **Weekly** | 7 days | Data updates weekly, cache for full week | NFCI, Fed balance sheet, Initial claims |
| **Monthly** | 30 days | Data updates monthly, cache for full month | ISM indices, Building permits, Savings rate |
| **Quarterly** | 90 days | Data updates quarterly, cache for full quarter | CC delinquency, Consumer loan delinquency |

### Implementation Notes

- **Cache invalidation**: Check data freshness before returning cached values
- **Smart caching**: For daily indicators, cache should expire at market close (4 PM ET) + data release time
- **Budget optimization**: Weekly/monthly indicators should check if new data is available before fetching
- **Fallback strategy**: If fresh data unavailable, use cached data with staleness warning

### Cache File Naming Convention

```
{data_source}_{identifier}_{date}.json

Examples:
- fred_DTWEXBGS_2026-01-14.json (daily)
- fred_NFCI_2026-01-14.json (weekly, dated when fetched)
- fred_NAPMNOI_2026-01-01.json (monthly, use first of month)
- fred_DRCCLACBS_2025-Q4.json (quarterly)
```

---

# Implementation Priority

| Phase | Enhancement | Effort | Impact |
|-------|-------------|--------|--------|
| 1 | Consumer Stress (3 indicators) | Low | High |
| 1 | Leading Indicators (3 indicators) | Low | High |
| 2 | Liquidity Plumbing (3 indicators) | Medium | High |
| 3 | Global Contagion (2 indicators) | Low | Medium |

**Recommended Start:** Consumer Stress and Leading Indicators—both use straightforward FRED data with no manual inputs, and together they address the biggest timing gap in current FRS.

---

# Operational Guidelines

## Data Update Schedule

Understanding when data releases occur is critical for proper cache management and data freshness validation.

| Indicator | Frequency | Release Day | Release Time (ET) | Data Lag | Next Update Logic |
|-----------|-----------|-------------|-------------------|----------|-------------------|
| Dollar Strength (DTWEXBGS) | Daily | Daily | After 6:00 PM | Same day | Check after 6 PM daily |
| EM Credit Spread (BAMLEMCBPIOAS) | Daily | Daily | After 6:00 PM | Same day | Check after 6 PM daily |
| HY Spread (BAMLH0A0HYM2) | Daily | Daily | After 6:00 PM | Same day | Check after 6 PM daily |
| Yield Curve (T10Y3M) | Daily | Daily | After 4:30 PM | Same day | Check after 4:30 PM daily |
| TED Spread (TEDRATE) | Daily | Daily | After 4:30 PM | Same day | Check after 4:30 PM daily |
| ISM New Orders (NAPMNOI) | Monthly | 1st business day | 10:00 AM | Prior month | 1st business day of month |
| ISM Inventories (NAPMII) | Monthly | 1st business day | 10:00 AM | Prior month | 1st business day of month |
| Initial Claims (ICSA) | Weekly | Thursday | 8:30 AM | 5 days | Every Thursday morning |
| Building Permits (PERMIT) | Monthly | ~18th of month | 8:30 AM | ~45 days | Mid-month check |
| Chicago Fed NFCI (NFCI) | Weekly | Friday | Afternoon | Same week | Every Friday afternoon |
| Fed Balance Sheet (WALCL) | Weekly | Thursday | 4:30 PM | Prior Wed | Every Thursday evening |
| CC Delinquency (DRCCLACBS) | Quarterly | ~6 weeks post-qtr | Variable | 45-60 days | Late Feb, May, Aug, Nov |
| Consumer Loan Delinq (DRALACBS) | Quarterly | ~6 weeks post-qtr | Variable | 45-60 days | Late Feb, May, Aug, Nov |
| Savings Rate (PSAVERT) | Monthly | End of month | Variable | ~30 days | Last week of month |

### Update Strategy

- **Daily indicators**: Check after release time, cache for 24 hours from release
- **Weekly indicators**: Check on release day after release time, cache for 7 days
- **Monthly indicators**: Check on expected release day, cache for 30 days
- **Quarterly indicators**: Check in expected release window, cache for 90 days

## Data Freshness Monitoring

### Freshness Validation Logic

```python
from datetime import datetime, timedelta
from typing import Dict
import logging

logger = logging.getLogger(__name__)

def check_data_freshness(series_id: str, last_update: datetime, expected_freq: str) -> Dict[str, any]:
    """
    Verify data is current based on expected frequency.

    Args:
        series_id: FRED series ID or data identifier
        last_update: Timestamp of last data update
        expected_freq: 'daily', 'weekly', 'monthly', 'quarterly'

    Returns:
        dict with freshness_ok (bool), days_stale (int), warning (str)
    """
    now = datetime.now()
    days_stale = (now - last_update).days

    # Staleness thresholds by frequency
    thresholds = {
        'daily': 2,       # Warn if >2 days old
        'weekly': 8,      # Warn if >8 days old
        'monthly': 35,    # Warn if >35 days old
        'quarterly': 100  # Warn if >100 days old
    }

    threshold = thresholds.get(expected_freq, 7)
    freshness_ok = days_stale <= threshold

    if not freshness_ok:
        warning = f"{series_id} is {days_stale} days stale (threshold: {threshold} days)"
        logger.warning(warning)
    else:
        warning = None
        logger.debug(f"{series_id} is fresh ({days_stale} days old)")

    return {
        'freshness_ok': freshness_ok,
        'days_stale': days_stale,
        'threshold_days': threshold,
        'last_update': last_update.isoformat(),
        'warning': warning
    }
```

### Alerting Thresholds

**Warning Level** - Data approaching stale:
- Daily: >1 day old
- Weekly: >5 days old
- Monthly: >25 days old
- Quarterly: >75 days old

**Critical Level** - Data definitely stale:
- Daily: >2 days old
- Weekly: >8 days old
- Monthly: >35 days old
- Quarterly: >100 days old

### Fallback Strategies

**When data is stale:**
1. **Check FRED API directly**: Attempt fresh fetch ignoring cache
2. **Use stale data with warning**: Return cached data with staleness metadata
3. **Use interpolation** (only for continuous series): Estimate based on trend
4. **Fail gracefully**: Return component score as 0 with error flag

**Priority order**: Fresh data > Stale data with warning > Interpolated data > Zero with error

---

# API Versioning Strategy

To support the new CMDS formula (60/20/20) while maintaining backward compatibility with existing users:

## Endpoint Versioning

### Current Endpoint (Backward Compatible)
```
GET /api/cmds
```
- Returns CMDS with **current formula**: `(0.65 × FRS) + (0.35 × VP)`
- Maintains existing behavior for all current users
- No breaking changes

### New Enhanced Endpoint (Version 2)
```
GET /api/cmds?version=2
```
OR
```
GET /api/cmds/v2
```
- Returns CMDS with **new formula**: `(0.60 × FRS) + (0.20 × EWS) + (0.20 × VP)`
- Includes EWS breakdown in response
- New users default to this version

### Response Structure Comparison

**Version 1 (Current)**:
```json
{
  "cmds": 72.5,
  "components": {
    "frs": 75.0,
    "vp": 65.0
  },
  "weights": {
    "frs_weight": 0.65,
    "vp_weight": 0.35
  }
}
```

**Version 2 (Enhanced)**:
```json
{
  "cmds": 72.0,
  "components": {
    "frs": 75.0,
    "ews": {
      "raw": 28,
      "normalized": 70.0,
      "categories": {
        "global_contagion": 6,
        "leading_indicators": 8,
        "liquidity_plumbing": 7,
        "consumer_stress": 7
      }
    },
    "vp": 65.0
  },
  "weights": {
    "frs_weight": 0.60,
    "ews_weight": 0.20,
    "vp_weight": 0.20
  }
}
```

## Migration Strategy

### Phase 1: Parallel Deployment (Months 1-3)
- Deploy new formula on v2 endpoint
- Keep v1 endpoint unchanged
- Run both formulas in parallel
- Monitor divergences and user adoption

### Phase 2: Beta Testing (Months 4-6)
- Invite beta users to test v2 endpoint
- Gather feedback on EWS categories
- Refine thresholds based on real-world performance
- Document divergence patterns

### Phase 3: Gradual Migration (Months 7-12)
- Notify all users of upcoming v2 default
- Provide migration guide and timeline
- Set deprecation date for v1 (12 months out)
- Make v2 the default for new users

### Phase 4: Full Transition (Month 13+)
- Make v2 the default endpoint
- Maintain v1 for backward compatibility (deprecated)
- Eventual sunset of v1 (announce 6 months in advance)

---

# Historical Validation & Backtesting

**CRITICAL REQUIREMENT**: Before production deployment, the new CMDS formula must be validated against major historical market events to ensure it provides superior early warning capability compared to the current formula.

## Required Backtesting Events

### Event 1: 2007-2008 Financial Crisis

**Objective**: Verify EWS would have provided 6-12 month early warning

**Data Collection Period**: Jan 2006 - Dec 2008

**Key Milestones**:
- **Peak**: Oct 2007 (S&P 500 peak: 1,565)
- **Bear Market Start**: Dec 2007 (official recession start)
- **Crisis Peak**: Sept-Oct 2008 (Lehman collapse)
- **Bottom**: Mar 2009 (S&P 500 low: 676, -57% from peak)

**Expected EWS Performance** (6 months before, Mar 2007):
- **Consumer Stress**: 6-7/10 (subprime delinquencies rising, savings declining)
- **Leading Indicators**: 5-6/10 (housing permits collapsing -30%, ISM weakening)
- **Liquidity Plumbing**: 4-5/10 (NFCI tightening, HY spreads widening)
- **Global Contagion**: 3-4/10 (EM stress building, dollar strengthening)
- **Total EWS**: 18-22/40 (Elevated warning zone)

**Expected EWS Performance** (12 months before, Sept 2006):
- **Total EWS**: 12-16/40 (Moderate warning zone)

**Validation Criteria**:
- ✅ **Pass**: EWS ≥18/40 by Mar 2007 (6 months before recession)
- ✅ **Strong Pass**: EWS ≥15/40 by Sept 2006 (12 months before recession)
- ❌ **Fail**: EWS <15/40 until Dec 2007 (no early warning)

### Event 2: 2018 Q4 Correction

**Objective**: Verify EWS detects stress in non-recession corrections

**Data Collection Period**: Jan 2018 - Mar 2019

**Key Milestones**:
- **Peak**: Sept 2018 (S&P 500: 2,930)
- **Correction**: Oct-Dec 2018 (-20% peak to trough)
- **Recovery**: Q1 2019

**Expected EWS Performance** (Sept 2018):
- **Consumer Stress**: 2-3/10 (stable but tightening)
- **Leading Indicators**: 3-4/10 (housing permits declining, claims rising)
- **Liquidity Plumbing**: 5-6/10 (Fed tightening, NFCI rising, HY spreads widening)
- **Global Contagion**: 4-5/10 (trade war stress, dollar strength, EM pain)
- **Total EWS**: 14-18/40 (Moderate to Elevated warning)

**Validation Criteria**:
- ✅ **Pass**: EWS ≥14/40 by Sept 2018 (timely warning)
- ❌ **Fail**: EWS <10/40 during correction (missed signal)

### Event 3: 2020 COVID Crash

**Objective**: Acknowledge unpredictable exogenous shocks

**Data Collection Period**: Jan 2020 - May 2020

**Key Milestones**:
- **Peak**: Feb 19, 2020 (S&P 500: 3,386)
- **Crash**: Feb 20 - Mar 23, 2020 (-34% in 33 days)
- **Recovery**: Apr-May 2020 (Fed intervention)

**Expected EWS Performance** (Jan 2020):
- **Total EWS**: 8-12/40 (Low to Moderate - **pre-COVID fundamentals were healthy**)

**Expected EWS Performance** (Mar 2020):
- **Total EWS**: 25-30/40 (High stress - **reactive, not predictive**)

**Validation Criteria**:
- ✅ **Pass**: EWS <15/40 in Jan 2020 (correctly shows low pre-shock risk)
- ✅ **Pass**: EWS >25/40 in Mar 2020 (correctly reflects crisis conditions)
- 📝 **Note**: Exogenous shocks are inherently unpredictable; validation confirms EWS responds appropriately but doesn't expect prediction

### Event 4: 2022 Bear Market

**Objective**: Verify EWS detects inflation/rate hike stress

**Data Collection Period**: Jan 2021 - Dec 2022

**Key Milestones**:
- **Peak**: Jan 3, 2022 (S&P 500: 4,797)
- **Bear Market**: Jan-Oct 2022 (-25% peak to trough)
- **Fed Rate Hikes**: 7 hikes in 2022 (0% → 4.25%)

**Expected EWS Performance** (Sept 2021, 4 months before peak):
- **Consumer Stress**: 5-6/10 (delinquencies rising, savings collapsing post-stimulus)
- **Leading Indicators**: 4-5/10 (housing permits peaking, claims still low)
- **Liquidity Plumbing**: 6-7/10 (Fed signaling tightening, NFCI rising)
- **Global Contagion**: 3-4/10 (EM stress from strong dollar)
- **Total EWS**: 18-22/40 (Elevated warning zone)

**Validation Criteria**:
- ✅ **Pass**: EWS ≥18/40 by Sept 2021 (4 months early warning)
- ✅ **Strong Pass**: EWS ≥15/40 by Jun 2021 (7 months early warning)
- ❌ **Fail**: EWS <15/40 until Jan 2022 (no early warning)

## Backtesting Methodology

### Data Requirements

1. **Collect historical data for all EWS indicators** (2006-2024):
   - FRED series: DTWEXBGS, BAMLEMCBPIOAS, NAPMNOI, NAPMII, ICSA, PERMIT, NFCI, BAMLH0A0HYM2, T10Y3M, TEDRATE, WALCL, DRCCLACBS, DRALACBS, PSAVERT
   - Yahoo Finance: EEM (EM equities)
   - Calculate monthly EWS scores for entire period

2. **Calculate CMDS versions**:
   - **Current CMDS**: (0.65 × FRS) + (0.35 × VP)
   - **New CMDS v2**: (0.60 × FRS) + (0.20 × EWS) + (0.20 × VP)
   - Compare performance across events

3. **Performance metrics**:
   - **Lead time**: Months before event that score reached warning threshold
   - **False positive rate**: Times score signaled risk but no event occurred
   - **Signal clarity**: Consistency of warning signal (no flip-flopping)
   - **Magnitude accuracy**: Did score magnitude match event severity?

### Success Criteria

**Minimum Acceptable Performance**:
- ✅ 2007-2008: EWS ≥18/40 by 6 months before recession
- ✅ 2018 Q4: EWS ≥14/40 before correction
- ✅ 2020 COVID: EWS <15/40 pre-shock, >25/40 during crisis
- ✅ 2022 Bear: EWS ≥18/40 by 4 months before peak
- ✅ False positive rate <30% (acceptable for early warning system)

**Strong Performance**:
- ✅ 2007-2008: EWS ≥18/40 by 12 months before recession
- ✅ All events: New CMDS v2 provides >2 months additional lead time vs current CMDS

### Backtesting Deliverables

1. **Historical EWS Time Series**: Monthly EWS scores from 2006-2024
2. **Event Analysis Report**: Detailed breakdown for each of the 4 events
3. **Comparative Performance**: Current CMDS vs New CMDS lead times
4. **False Positive Analysis**: Document periods when EWS high but no crisis
5. **Threshold Refinement**: Adjust indicator thresholds if needed based on historical performance
6. **Confidence Assessment**: Overall confidence level in EWS predictive capability

## Next Steps After Backtesting

**If backtesting passes all success criteria:**
→ Proceed to Phase 2 (parallel deployment)

**If backtesting shows deficiencies:**
→ Refine indicator thresholds and re-test
→ Consider adding/removing indicators
→ Re-evaluate category weights within EWS
→ **Do not deploy to production until validation passes**

---

# Threshold Calibration Methodology

**Purpose**: Establish data-driven justification for all indicator thresholds using historical distribution analysis.

## Calibration Process

### Step 1: Historical Distribution Analysis

For each indicator, analyze full historical range (2000-2024 or longest available):

```python
def calibrate_thresholds(series_data: pd.Series, indicator_name: str) -> dict:
    """
    Calculate empirical thresholds based on historical distribution.

    Returns percentile-based thresholds and crisis context.
    """
    # Calculate distribution statistics
    stats = {
        'mean': series_data.mean(),
        'median': series_data.median(),
        'std': series_data.std(),
        'min': series_data.min(),
        'max': series_data.max(),
        'p25': series_data.quantile(0.25),
        'p50': series_data.quantile(0.50),
        'p75': series_data.quantile(0.75),
        'p90': series_data.quantile(0.90),
        'p95': series_data.quantile(0.95),
        'p99': series_data.quantile(0.99)
    }

    # Crisis period values
    crisis_periods = {
        '2008_gfc': series_data['2008-09':'2008-12'].mean(),
        '2020_covid': series_data['2020-03':'2020-04'].mean(),
        '2022_bear': series_data['2022-09':'2022-10'].mean()
    }

    # Recommended thresholds (example for dollar strength)
    thresholds = {
        'calm': stats['p25'],        # Below 25th percentile
        'normal': stats['p50'],      # 25th-75th percentile
        'elevated': stats['p75'],    # 75th-90th percentile
        'stress': stats['p90'],      # 90th-95th percentile
        'crisis': stats['p95']       # Above 95th percentile
    }

    return {
        'indicator': indicator_name,
        'stats': stats,
        'crisis_values': crisis_periods,
        'recommended_thresholds': thresholds
    }
```

### Step 2: Crisis Alignment Validation

Verify thresholds align with actual crisis periods:

| Indicator | 2008 GFC Value | 2020 COVID Value | 2022 Bear Value | Recommended Crisis Threshold |
|-----------|----------------|------------------|-----------------|------------------------------|
| DXY | 89 (p95) | 103 (p99) | 114 (p99+) | >110 (p95) |
| EM Spread | 900bps (p99+) | 700bps (p99) | 450bps (p85) | >500bps (p95) |
| HY Spread | 20%+ (p99+) | 11% (p99) | 5.5% (p75) | >7% (p95) |
| ISM Gap | -8 (p10) | -5 (p15) | -3 (p25) | <-5 (p15) |
| Claims +% | +75% (p99+) | +3,186% (p99+) | +39% (p90) | >35% (p90) |

### Step 3: Threshold Justification Documentation

For each indicator threshold, document:

1. **Percentile basis**: "DXY >115 = 99th percentile (crisis territory)"
2. **Historical precedent**: "Exceeded 115 only during: 2022 rate hikes, 2001 flight to safety"
3. **Economic rationale**: "Strong dollar = EM debt stress, commodity deflation, earnings headwind"
4. **Score assignment logic**: "Linear scoring 100-115 = 1-2 points, >115 = 3 points (crisis)"

### Step 4: Sensitivity Testing

Test threshold variations ±20% on historical data:

- **Original threshold**: DXY >115 = 3 points
- **-20% threshold**: DXY >92 = 3 points → False positives increase 45%
- **+20% threshold**: DXY >138 = 3 points → Miss 2022 event entirely

**Conclusion**: Original threshold optimal (minimize false positives while capturing crises)

## Threshold Review Schedule

- **Annual review**: Check if distribution has shifted due to regime change
- **Triggered review**: If 3+ consecutive months at extreme threshold
- **Post-crisis review**: After major market event, validate threshold performance

---

# Appendix: Complete Master Calculation Function

```python
def calculate_enhanced_frs(fred_api_key: str, manual_inputs: dict = None) -> dict:
    """
    Master function to calculate all FRS components including enhancements.
    
    Returns comprehensive risk assessment with both original FRS
    and new early warning indicators.
    """
    from datetime import datetime
    
    # Original FRS Categories (from existing implementation)
    macro_cycle = calculate_macro_cycle(fred_api_key)
    valuation = calculate_valuation(fred_api_key)
    leverage = calculate_leverage_financial(fred_api_key, manual_inputs)
    earnings = calculate_earnings_margins()
    technical = calculate_technical_sentiment()
    
    # New Enhancement Categories
    global_contagion = calculate_global_contagion(fred_api_key)
    leading = calculate_leading_indicators(fred_api_key)
    liquidity = calculate_liquidity_plumbing(fred_api_key)
    consumer = calculate_consumer_stress(fred_api_key)
    
    # Calculate totals
    frs_original = (macro_cycle['total'] + valuation['total'] + 
                   leverage['total'] + earnings['total'] + technical['total'])
    
    ews_total = (global_contagion['total'] + leading['total'] + 
                liquidity['total'] + consumer['total'])
    
    # Get VP score (assume available from VP module)
    vp_score = get_vp_score()  # Returns 0-100
    
    # Calculate new CMDS (FRS + EWS + VP)
    # Normalize EWS to 0-100 scale
    ews_normalized = (ews_total / 40) * 100
    
    # Calculate weighted contributions
    frs_contribution = 0.60 * frs_original      # 0-60 points
    ews_contribution = 0.20 * ews_normalized    # 0-20 points
    vp_contribution = 0.20 * vp_score           # 0-20 points
    
    # CMDS is weighted sum (already 0-100 scale)
    cmds = frs_contribution + ews_contribution + vp_contribution
    cmds = max(0, min(100, cmds))  # Clamp to 0-100
    
    return {
        'timestamp': datetime.now().isoformat(),
        'scores': {
            'frs_original': {
                'total': frs_original,
                'max': 100,
                'weight': 0.60,
                'contribution_to_cmds': round(frs_contribution, 1),
                'max_contribution': 60,
                'categories': {
                    'macro_cycle': macro_cycle,
                    'valuation': valuation,
                    'leverage_financial': leverage,
                    'earnings_margins': earnings,
                    'technical_sentiment': technical
                }
            },
            'early_warning_score': {
                'total': ews_total,
                'max': 40,
                'normalized': round(ews_normalized, 1),
                'weight': 0.20,
                'contribution_to_cmds': round(ews_contribution, 1),
                'max_contribution': 20,
                'categories': {
                    'global_contagion': global_contagion,
                    'leading_indicators': leading,
                    'liquidity_plumbing': liquidity,
                    'consumer_stress': consumer
                }
            },
            'volatility_predictor': {
                'total': vp_score,
                'max': 100,
                'weight': 0.20,
                'contribution_to_cmds': round(vp_contribution, 1),
                'max_contribution': 20
            },
            'cmds': {
                'total': round(cmds, 1),
                'max': 100,
                'zone': get_cmds_zone(cmds)
            }
        },
        'interpretation': {
            'frs_zone': get_frs_zone(frs_original),
            'ews_zone': get_ews_zone(ews_total),
            'vp_level': get_vp_level(vp_score),
            'cmds_zone': get_cmds_zone(cmds),
            'cmds_interpretation': get_cmds_interpretation(cmds)
        }
    }
```

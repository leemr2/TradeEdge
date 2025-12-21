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
- **New CMDS Formula:** CMDS = (0.65 × FRS) + (0.20 × EWS_normalized) + (0.15 × VP)
  - FRS contributes 65%: `0.65 × FRS` (FRS is 0-100)
  - EWS contributes 20%: `0.20 × (EWS_raw / 40) × 100` (EWS normalized to 0-100)
  - VP contributes 15%: `0.15 × VP` (VP is 0-100)
  - CMDS final score: 0-100 scale (weighted sum)

---

## New CMDS Formula Overview

**Current CMDS (to be replaced):**
```
CMDS = (0.65 × FRS) + (0.35 × VP)
```

**New CMDS Formula:**
```
CMDS = (0.65 × FRS) + (0.20 × EWS_normalized) + (0.15 × VP)
```

### Detailed Calculation

1. **Fundamental Risk Score (FRS)**: 0-100 points
   - Macro/Cycle: 0-30 points
   - Valuation: 0-25 points
   - Leverage & Stability: 0-25 points
   - Earnings & Margins: 0-10 points
   - Sentiment: -10 to +10 points
   - **FRS Contribution to CMDS**: `0.65 × FRS` = 0-65 points

2. **Early Warning Score (EWS)**: 0-40 points
   - Global Contagion: 0-10 points
   - Leading Indicators: 0-10 points
   - Liquidity Plumbing: 0-10 points
   - Consumer Stress: 0-10 points
   - **EWS Normalized**: `(EWS_raw / 40) × 100` = 0-100 scale
   - **EWS Contribution to CMDS**: `0.20 × EWS_normalized` = 0-20 points

3. **Volatility Predictor (VP)**: 0-100 points
   - Fear keyword composite, search volatility, cross-asset stress
   - **VP Contribution to CMDS**: `0.15 × VP` = 0-15 points

4. **CMDS Final Score**: `FRS_contribution + EWS_contribution + VP_contribution` = 0-100 scale

### Weight Distribution

| Component | Raw Range | Normalized Range | Weight | Contribution Range | Rationale |
|-----------|-----------|-----------------|--------|-------------------|-----------|
| FRS | 0-100 | 0-100 | 65% | 0-65 points | Fundamental structural risk assessment |
| EWS | 0-40 | 0-100 | 20% | 0-20 points | Early warning signals (3-12 month lead time) |
| VP | 0-100 | 0-100 | 15% | 0-15 points | Timing precision and sentiment shifts |
| **Total** | - | - | **100%** | **0-100** | Weighted sum, no normalization needed |

### Why This Approach?

- **FRS remains primary**: 65% weight reflects fundamental structural risk as the foundation
- **EWS adds early warning**: 20% weight provides 3-12 months lead time on deterioration
- **VP provides timing**: 15% weight catches sentiment shifts and short-term risk spikes
- **Comprehensive coverage**: Fundamental assessment (FRS) + Early warnings (EWS) + Timing (VP) = complete risk picture
- **Maintains CMDS scale**: Final score remains 0-100 for consistency with existing allocation zones

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

## Indicator 3.2: Treasury Market Stress / MOVE Index (0-3 points)

### Concept

The MOVE Index is the "VIX for bonds"—it measures implied volatility in Treasury options. Treasury market stress matters because:
- Treasuries are the global risk-free benchmark
- Treasury dysfunction spreads to all asset classes
- Dealer balance sheet constraints amplify moves
- Fed may need to intervene (as in 2020, 2023)

### Data Source

**Yahoo Finance:** `^MOVE`
- **Full Name:** ICE BofA MOVE Index
- **Frequency:** Real-time during market hours
- **Note:** MOVE is not available on FRED; use Yahoo Finance

### Calculation Method

```python
def score_treasury_stress(self) -> tuple:
    """
    Score based on MOVE Index level.
    Higher MOVE = more Treasury market stress.
    """
    move = yf.Ticker('^MOVE')
    hist = move.history(period='1y')
    
    current_move = hist['Close'].iloc[-1]
    avg_move_1y = hist['Close'].mean()
    high_move_1y = hist['Close'].max()
    
    # Historical context: MOVE long-term average ~90-100
    if current_move < 90:
        score = 0  # Low volatility, calm
    elif current_move < 110:
        score = 1  # Normal range
    elif current_move < 140:
        score = 2  # Elevated stress
    else:  # >= 140
        score = 3  # Crisis-level volatility
    
    data = {
        'current_move': round(current_move, 1),
        'avg_move_1y': round(avg_move_1y, 1),
        'high_move_1y': round(high_move_1y, 1),
        'percentile_1y': round((hist['Close'] < current_move).mean() * 100, 0)
    }
    
    return score, data
```

### Scoring Thresholds

| Score | MOVE Level | Interpretation |
|-------|------------|----------------|
| 0 | <90 | Calm Treasury market |
| 1 | 90-110 | Normal volatility |
| 2 | 110-140 | Elevated stress |
| 3 | >140 | Crisis conditions |

### Historical MOVE Spikes

| Period | MOVE Peak | Context |
|--------|-----------|---------|
| 2008 GFC | 264 | Treasury market seized |
| 2020 COVID | 164 | Fed intervention needed |
| 2022 UK Pension | 160 | Global bond selloff |
| 2023 SVB/Banking | 199 | Flight to/from quality |

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
    move_score, move_data = score_treasury_stress()
    fed_score, fed_data = score_fed_balance_sheet(fred_api_key)
    
    total = min(10, fci_score + move_score + fed_score)
    
    return {
        'total': total,
        'max_points': 10,
        'indicators': {
            'financial_conditions': {'score': fci_score, 'data': fci_data},
            'treasury_stress': {'score': move_score, 'data': move_data},
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
    - FRS contributes 65%: 0.65 × FRS (FRS is 0-100)
    - EWS contributes 20%: 0.20 × (EWS_raw / 40) × 100 (EWS normalized to 0-100)
    - VP contributes 15%: 0.15 × VP (VP is 0-100)
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
    frs_contribution = 0.65 * frs_score           # 0-65 points
    ews_contribution = 0.20 * ews_normalized       # 0-20 points
    vp_contribution = 0.15 * vp_score              # 0-15 points
    
    # CMDS is weighted sum (already 0-100 scale)
    cmds = frs_contribution + ews_contribution + vp_contribution
    cmds = max(0, min(100, cmds))  # Clamp to 0-100
    
    return {
        'cmds': round(cmds, 1),
        'components': {
            'frs': {
                'raw': round(frs_score, 1),
                'max': 100,
                'weight': 0.65,
                'contribution': round(frs_contribution, 1),
                'max_contribution': 65
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
                'weight': 0.15,
                'contribution': round(vp_contribution, 1),
                'max_contribution': 15
            }
        },
        'weights': {
            'frs_weight': 0.65,
            'ews_weight': 0.20,
            'vp_weight': 0.15
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
FRS Contribution = 0.65 × 75 = 48.75 points
EWS Normalized   = (28 / 40) × 100 = 70.0
EWS Contribution = 0.20 × 70.0 = 14.0 points
VP Contribution  = 0.15 × 65 = 9.75 points
CMDS             = 48.75 + 14.0 + 9.75 = 72.5 → 73/100

Zone: HIGH (30-50% equity allocation)
```

### Rationale for New CMDS Formula

**Why FRS + EWS + VP:**
- **FRS remains foundation (65%)**: Fundamental structural risk assessment is the primary driver of long-term risk
- **EWS adds early warning (20%)**: Leading indicators detect deterioration 3-12 months before lagging indicators, providing actionable lead time
- **VP provides timing precision (15%)**: Volatility Predictor catches sentiment shifts and short-term risk spikes for optimal entry/exit timing
- **Comprehensive coverage**: Fundamental assessment (FRS) + Early warnings (EWS) + Timing (VP) = complete risk picture

**Why 65% FRS + 20% EWS + 15% VP:**
- FRS gets majority weight because fundamentals determine the magnitude of potential corrections
- EWS gets meaningful weight (20%) to provide early warning signals without overwhelming the fundamental assessment
- VP gets focused weight (15%) to add timing precision while maintaining emphasis on structural risk
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
| MOVE Index | Yahoo | ^MOVE | Real-time |
| Fed Balance Sheet | FRED | WALCL | Weekly |
| CC Delinquency | FRED | DRCCLACBS | Quarterly |
| Consumer Loan Delinq | FRED | DRALACBS | Quarterly |
| Savings Rate | FRED | PSAVERT | Monthly |

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
    frs_contribution = 0.65 * frs_original      # 0-65 points
    ews_contribution = 0.20 * ews_normalized    # 0-20 points
    vp_contribution = 0.15 * vp_score           # 0-15 points
    
    # CMDS is weighted sum (already 0-100 scale)
    cmds = frs_contribution + ews_contribution + vp_contribution
    cmds = max(0, min(100, cmds))  # Clamp to 0-100
    
    return {
        'timestamp': datetime.now().isoformat(),
        'scores': {
            'frs_original': {
                'total': frs_original,
                'max': 100,
                'weight': 0.65,
                'contribution_to_cmds': round(frs_contribution, 1),
                'max_contribution': 65,
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
                'weight': 0.15,
                'contribution_to_cmds': round(vp_contribution, 1),
                'max_contribution': 15
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

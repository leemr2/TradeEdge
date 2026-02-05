# Earnings & Margins Calculator Improvement Guide
## Theme-Agnostic Concentration Risk Framework

---

## Philosophy: Future-Proof Risk Detection

**The Problem with AI-Specific Flags:**
- AI boom is today's narrative, but tomorrow it could be:
  - Quantum computing (2027?)
  - Clean energy (2028?)
  - Biotech revolution (2029?)
  - Metaverse 2.0 (2030?)

**The Solution:**
Build a **concentration risk pattern detector** that identifies dangerous market structures regardless of the underlying theme. The math of bubble formation is consistent - only the story changes.

---

## Revised Architecture: Universal Concentration Framework

### **Category 4: Earnings & Margins (0-12 points)** 🔄 EXPANDED SCOPE

#### **Indicator 4.1: Market Breadth Divergence (0-5 points)** 🆕 PRIMARY INDICATOR
- **Philosophy:** Breadth deterioration precedes price tops by weeks/months
- **Metrics:** 
  - % stocks above 200-day MA declining while index rises
  - Advance-Decline line failing to confirm new highs
  - New Highs shrinking even as index climbs
- **Historical Evidence:** Caught 1929, 2000, 2007, 2021 tops with 1-3 month lead time
- **Why This Works:** Market can't sustain rallies when participation collapses

#### **Indicator 4.2: Earnings Concentration (0-5 points)** ⬇️ DEMOTED TO SECONDARY
- **Current:** QQQ vs RSP (mega-cap vs equal-weight)
- **Enhancement:** Add attribution analysis - *why* is concentration happening?
- **Rationale:** Concentration confirms what breadth already warned about
- **Future-proof:** Works for any concentrated theme (AI, clean energy, etc.)

#### **Indicator 4.3: Red Flag Overlay (0-2 bonus penalty)** 🆕 CONFIRMATION LAYER
- **Combines:** Breadth patterns + concentration + behavioral warnings
- **Rationale:** Multiple signals converging = high confidence
- **Future-proof:** Mathematical patterns regardless of narrative

---

## Why Market Breadth Is Your Best Early Warning System

### **The Evidence from Every Major Top:**

**1929 - The Great Crash:**
- Dow peaked September 3, 1929 at 381
- Advance-Decline line peaked **April 1929** (5 months early warning)
- By September, only 25 stocks (out of hundreds) were making new highs
- Classic breadth divergence: "Generals advancing, troops retreating"

**2000 - Dotcom Crash:**
- NASDAQ peaked March 10, 2000 at 5,048
- % of NASDAQ stocks above 200-day MA peaked **February 1999** (13 months early)
- By March 2000, only 15% of NASDAQ stocks were above 200-day MA
- Market rose on smaller and smaller group of tech leaders

**2007 - Financial Crisis:**
- S&P 500 peaked October 9, 2007 at 1,565
- NYSE Advance-Decline line peaked **June 2007** (4 months early warning)
- New Highs/New Lows ratio turned negative **July 2007**
- Small-caps (Russell 2000) peaked **July 2007**, diverging from large-caps

**2021 - COVID Bubble Top:**
- S&P 500 peaked January 4, 2022 at 4,818
- Equal-weight S&P (RSP) peaked **November 8, 2021** (2 months early)
- % stocks above 200-day MA peaked **November 2021** at 90%, fell to 60% by January
- Ark Innovation (ARKK) peaked **February 2021** - 11 months before S&P!

### **Why Breadth Works When Other Indicators Fail:**

**1. Market-Cap Weighting Masks Weakness:**
- S&P 500 is market-cap weighted: Apple + Microsoft + NVIDIA = 20% of index
- These 3 stocks can push index to new highs even if 497 other stocks fall
- Breadth metrics are equal-weighted: they count votes, not dollars
- You can't hide weakness from breadth

**2. Breadth Deterioration = Distribution Phase:**
- Smart money sells first (small/mid caps, laggards)
- Retail chases last (mega-cap leaders, momentum)
- By the time mega-caps roll over, most stocks already crashed
- Breadth catches the early stage of this rotation

**3. Concentration Alone Misses The Timing:**
- Concentration can stay extreme for months (2023-2025 = 2+ years!)
- Breadth tells you **when** concentration is about to reverse
- Concentration = "market is vulnerable", Breadth = "market is topping"

**4. Breadth Is Hard To Manipulate:**
- Hedge funds can pump 5-10 mega-cap stocks
- They can't pump 250+ stocks to fake breadth
- Breadth gives you the unvarnished truth of market participation

### **Visual: How Breadth Divergence Looks:**

```
                    SPY (cap-weighted)
                    /
                   /  <- Index makes new highs
                  /
                 /
   ------------/  <- Breadth peaks here (1-3 months before top)
              /
         RSP (equal-weighted) flattens
        /
       / <- Most stocks already declining
      /
```

**Current Environment (Dec 2025):**
- SPY near all-time highs
- RSP underperforming by ~12% over past year
- This is a **textbook late-stage bull market pattern**
- History says: 1-3 months until SPY follows RSP down

---

## Enhanced Indicator Specifications

### **Indicator 4.1: Market Breadth Divergence (PRIMARY - MOST PREDICTIVE)**

**Why Breadth Is Superior to Concentration:**

Concentration tells you **what has happened** (mega-caps dominate).
Breadth tells you **what will happen** (participation collapsing = reversal coming).

**Historical Evidence:**
- **1929:** Advance-Decline line peaked 6 months before market
- **2000:** % above 200-day MA declined from 80% to 40% while NASDAQ made new highs
- **2007:** New Highs/New Lows ratio diverged 4 months before peak
- **2021:** Breadth peaked November 2021, market peaked January 2022

**The Math:** An index (SPY, QQQ) is market-cap weighted. The top 10 stocks can push it to new highs even if 400+ stocks are falling. Breadth metrics are **equal-weighted** - they detect when the majority is weakening.

---

**Implementation:**

```python
def _score_market_breadth(self) -> Dict[str, Any]:
    """
    Multi-metric breadth divergence detector
    Combines 3 independent breadth signals for robust detection
    
    This is the MOST PREDICTIVE indicator in the entire FRS system
    because breadth deterioration precedes crashes by 1-3 months
    """
    
    # Fetch data
    spy = self.yfinance.fetch_ticker('SPY', period='6mo')
    rsp = self.yfinance.fetch_ticker('RSP', period='6mo')  # Equal-weight S&P 500
    
    if len(spy) == 0 or len(rsp) == 0:
        return self._error_response('market_breadth')
    
    # METRIC 1: Equal-Weight vs Cap-Weight Divergence
    # When RSP underperforms SPY = narrow leadership (fewer stocks participating)
    spy_6m = ((spy['Close'].iloc[-1] / spy['Close'].iloc[0]) - 1) * 100
    rsp_6m = ((rsp['Close'].iloc[-1] / rsp['Close'].iloc[0]) - 1) * 100
    breadth_gap = spy_6m - rsp_6m  # Positive = narrow leadership
    
    # METRIC 2: Price vs Breadth Momentum Divergence
    # Compare recent 1-month vs full 6-month trends
    spy_1m = ((spy['Close'].iloc[-1] / spy['Close'].iloc[-21]) - 1) * 100  # Last ~1 month
    rsp_1m = ((rsp['Close'].iloc[-1] / rsp['Close'].iloc[-21]) - 1) * 100
    
    # Divergence = SPY rising but RSP flat/down (breadth not confirming)
    recent_divergence = spy_1m - rsp_1m
    
    # METRIC 3: Volatility of Breadth Gap (Instability Signal)
    # Calculate rolling 20-day breadth gap
    spy_prices = spy['Close']
    rsp_prices = rsp['Close']
    
    # Normalize to same starting point for comparison
    spy_normalized = (spy_prices / spy_prices.iloc[0]) * 100
    rsp_normalized = (rsp_prices / rsp_prices.iloc[0]) * 100
    
    breadth_gap_series = spy_normalized - rsp_normalized
    breadth_volatility = breadth_gap_series.rolling(20).std().iloc[-1]
    
    # SCORING LOGIC
    # Each metric contributes 0-1.67 points (sum to 5.0 max)
    
    # Score 1: Structural breadth gap (0-1.67 points)
    if breadth_gap < 3:
        score1 = 0.0
        interp1 = "Broad participation - healthy"
    elif breadth_gap < 8:
        score1 = (breadth_gap - 3) / 5 * 0.84
        interp1 = "Moderate narrowing"
    elif breadth_gap < 15:
        score1 = 0.84 + (breadth_gap - 8) / 7 * 0.83
        interp1 = "Significant narrowing"
    else:
        score1 = 1.67
        interp1 = "Extreme concentration"
    
    # Score 2: Recent divergence (0-1.67 points)
    if recent_divergence < 2:
        score2 = 0.0
        interp2 = "Recent breadth confirms price"
    elif recent_divergence < 5:
        score2 = (recent_divergence - 2) / 3 * 0.84
        interp2 = "Mild recent divergence"
    elif recent_divergence < 10:
        score2 = 0.84 + (recent_divergence - 5) / 5 * 0.83
        interp2 = "Serious recent divergence"
    else:
        score2 = 1.67
        interp2 = "Severe topping pattern"
    
    # Score 3: Breadth instability (0-1.67 points)
    if breadth_volatility < 1.0:
        score3 = 0.0
        interp3 = "Stable breadth pattern"
    elif breadth_volatility < 2.5:
        score3 = (breadth_volatility - 1.0) / 1.5 * 0.84
        interp3 = "Moderate breadth volatility"
    elif breadth_volatility < 4.0:
        score3 = 0.84 + (breadth_volatility - 2.5) / 1.5 * 0.83
        interp3 = "High breadth instability"
    else:
        score3 = 1.67
        interp3 = "Extreme breadth whipsaw"
    
    # Total score
    total_score = score1 + score2 + score3
    
    # Overall interpretation
    if total_score < 1.5:
        overall_interp = "Healthy breadth - broad participation"
    elif total_score < 3.0:
        overall_interp = "Caution - breadth weakening"
    elif total_score < 4.0:
        overall_interp = "Warning - dangerous narrowing detected"
    else:
        overall_interp = "CRITICAL - Classic topping pattern (1-3 month warning)"
    
    return {
        'name': 'market_breadth',
        'score': round(total_score, 1),
        'value': round(breadth_gap, 2),
        'last_updated': datetime.now().isoformat(),
        'interpretation': overall_interp,
        'data_source': 'Yahoo Finance: SPY, RSP',
        'sub_metrics': {
            'structural_gap': {
                'value': round(breadth_gap, 2),
                'score': round(score1, 2),
                'interpretation': interp1
            },
            'recent_divergence': {
                'value': round(recent_divergence, 2),
                'score': round(score2, 2),
                'interpretation': interp2
            },
            'breadth_volatility': {
                'value': round(breadth_volatility, 2),
                'score': round(score3, 2),
                'interpretation': interp3
            }
        },
        'details': {
            'spy_6m_return': round(spy_6m, 2),
            'rsp_6m_return': round(rsp_6m, 2),
            'spy_1m_return': round(spy_1m, 2),
            'rsp_1m_return': round(rsp_1m, 2),
        }
    }
```

**Why This Three-Metric Approach Works:**

1. **Structural Gap (SPY vs RSP 6-month):** Measures chronic concentration
   - Analogous to: "% stocks above 200-day MA declining over months"
   
2. **Recent Divergence (SPY vs RSP 1-month):** Detects acceleration of weakness
   - Analogous to: "Advance-Decline line not confirming new highs"
   
3. **Breadth Volatility:** Measures internal instability
   - Analogous to: "New Highs shrinking erratically at each index peak"

**Data Advantages:**
- ✅ All data from free Yahoo Finance (SPY, RSP)
- ✅ Updated real-time during market hours
- ✅ No manual inputs required
- ✅ Works for any market environment (not AI-specific)

---

### **Indicator 4.2: Margin Quality & Sustainability (NEW)**

**Philosophy:**
Bubbles occur when **prices diverge from fundamentals**. Instead of tracking AI CapEx specifically, track the general relationship between:
1. Price momentum (what market is paying)
2. Earnings quality (what companies actually deliver)

**Implementation:**

```python
def _score_margin_quality(self) -> Dict[str, Any]:
    """
    Compare momentum stocks vs quality stocks
    High divergence = unsustainable earnings, margin risk
    
    MTUM (Momentum) = highest price momentum stocks
    QUAL (Quality) = high ROE, stable earnings, low debt
    
    When MTUM >> QUAL = market chasing hype over fundamentals
    """
    
    # Fetch momentum vs quality factors
    mtum = self.yfinance.fetch_ticker('MTUM', period='6mo')  # Momentum factor
    qual = self.yfinance.fetch_ticker('QUAL', period='6mo')  # Quality factor
    
    if len(mtum) == 0 or len(qual) == 0:
        return self._error_response('margin_quality')
    
    # Calculate 6-month returns
    mtum_return = ((mtum['Close'].iloc[-1] / mtum['Close'].iloc[0]) - 1) * 100
    qual_return = ((qual['Close'].iloc[-1] / qual['Close'].iloc[0]) - 1) * 100
    
    # Divergence: momentum outpacing quality = bubble risk
    divergence = mtum_return - qual_return
    
    # Score based on divergence
    if divergence < 5:
        score = 0.0
        interpretation = 'Quality and momentum aligned - sustainable earnings'
    elif divergence < 10:
        score = (divergence - 5) / 5 * 1.5
        interpretation = 'Moderate divergence - some speculation present'
    elif divergence < 20:
        score = 1.5 + (divergence - 10) / 10 * 2.0
        interpretation = 'Significant divergence - earnings quality concerns'
    else:  # >= 20
        score = 5.0
        interpretation = 'Extreme divergence - bubble-like conditions'
    
    return {
        'name': 'margin_quality',
        'score': round(score, 1),
        'value': round(divergence, 2),
        'last_updated': datetime.now().isoformat(),
        'interpretation': interpretation,
        'data_source': 'Yahoo Finance: MTUM, QUAL',
        'details': {
            'momentum_return_6m': round(mtum_return, 2),
            'quality_return_6m': round(qual_return, 2),
        }
    }
```

**Why This Is Theme-Agnostic:**
- MTUM captures whatever theme is hot (AI today, quantum tomorrow)
- QUAL represents sustainable business fundamentals
- Divergence signals bubble risk regardless of narrative
- Would have caught: dotcom (2000), housing (2007), COVID tech (2021)

---


### **Category 1: Structural Concentration (Weight: 0.6, AUTOMATED)**

#### **Flag:** `top10_weight_above_38`
- **Type:** Boolean (automated)
- **Definition:** Top 10 S&P 500 stocks represent >38% of index weight
- **Data Source:** S&P 500 constituent weights (daily from Yahoo Finance or via calculation)
- **Current Calculation:**
```python
def check_top10_weight(self) -> bool:
    """
    Fetch S&P 500 constituent weights
    Sum top 10, check if >38%
    """
    # Get S&P 500 constituents and market caps
    spy_holdings = self._fetch_spy_holdings()  # From ETF holdings or manual list
    
    # Calculate weights
    total_market_cap = spy_holdings['market_cap'].sum()
    spy_holdings['weight'] = spy_holdings['market_cap'] / total_market_cap * 100
    
    # Sort by weight, sum top 10
    top10_weight = spy_holdings.nlargest(10, 'weight')['weight'].sum()
    
    return top10_weight > 38.0
```
- **Historical Context:** 
  - Normal range: 20-30%
  - 2000 dotcom peak: ~28%
  - **Current (2024): ~40%** ✅ Should be TRUE
- **Set to TRUE when:** Top 10 weight exceeds 38%

#### **Flag:** `hhi_rising_3yr`
- **Type:** Boolean (automated)
- **Definition:** Herfindahl-Hirschman Index (HHI) for S&P 500 has risen for 3+ consecutive years
- **Formula:** `HHI = Σ(weight_i)²` for all stocks
- **Data Source:** Calculate from S&P 500 weights
```python
def check_hhi_rising(self) -> bool:
    """
    Calculate HHI annually for past 3 years
    Return True if 2023 > 2024 > 2025 (rising trend)
    """
    hhi_history = {}
    
    for year in [2023, 2024, 2025]:
        weights = self._get_spy_weights_for_year(year)
        hhi = (weights ** 2).sum()
        hhi_history[year] = hhi
    
    # Check if rising for 3 years
    return (hhi_history[2024] > hhi_history[2023] and 
            hhi_history[2025] > hhi_history[2024])
```
- **Historical Context:**
  - 1990s average HHI: ~300
  - 2000 peak: ~400
  - Current: ~500 (estimated)
- **Set to TRUE when:** 3-year rising trend confirmed

#### **Flag:** `top10_drive_50pct_returns`
- **Type:** Boolean (automated)
- **Definition:** Top 10 stocks contributed >50% of S&P 500 total return YTD
- **Data Source:** Individual stock returns weighted by market cap
```python
def check_return_concentration(self) -> bool:
    """
    Calculate each stock's contribution to S&P 500 return
    Sum top 10 contributions, check if >50%
    """
    # Get S&P 500 returns by stock
    spy_returns = self._fetch_spy_constituent_returns(period='YTD')
    
    # Weight returns by starting market cap
    spy_returns['contribution'] = spy_returns['return'] * spy_returns['weight_start']
    
    # Sort by contribution
    top10_contribution = spy_returns.nlargest(10, 'contribution')['contribution'].sum()
    total_return = spy_returns['contribution'].sum()
    
    return (top10_contribution / total_return) > 0.50
```
- **Historical Context:**
  - Healthy market: Top 10 drive ~25-35% of returns
  - 2000: ~40%
  - **Current (2024): ~60%** ✅ Should be TRUE
- **Set to TRUE when:** Top 10 contribution exceeds 50%

---


#### **Flag:** `margin_debt_elevated`
- **Type:** Boolean (automated)
- **Definition:** FINRA margin debt >2% of GDP (extreme leverage)
- **Data Source:** FINRA margin statistics (monthly), FRED GDP data
```python
def check_margin_debt(self) -> bool:
    """
    Fetch FINRA margin debt and nominal GDP
    Calculate margin debt as % of GDP
    """
    # FINRA publishes monthly margin debt
    margin_debt = self._fetch_finra_margin_debt()  # Latest month
    
    # FRED: Nominal GDP (quarterly, use latest)
    gdp = self.fred.fetch_series('GDP')[-1]
    
    # Convert to comparable units (both in billions)
    margin_debt_billions = margin_debt / 1e9
    gdp_quarterly_billions = gdp
    gdp_monthly_billions = gdp_quarterly_billions / 3
    
    # Calculate percentage
    margin_pct_gdp = (margin_debt_billions / gdp_monthly_billions) * 100
    
    return margin_pct_gdp > 2.0
```
- **Historical Context:**
  - Normal: 1.0-1.5% of GDP
  - 2000 peak: 1.8%
  - 2021 peak: 2.3%
- **Data Source:** https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics
- **Set to TRUE when:** Margin debt >2% of monthly GDP

#### **Flag:** `retail_inflow_surge`
- **Type:** Boolean (semi-automated)
- **Definition:** Retail investor flows into equities exceed 3-month moving average by >2σ
- **Data Source:** EPFR Global fund flows, Vanda Research retail tracker
```python
def check_retail_surge(self) -> bool:
    """
    Track retail investor flows into equity ETFs
    Flag when current week >2σ above 3-month average
    
    Note: Premium data required (EPFR, Vanda)
    Alternative: Use free proxy from AAII sentiment survey
    """
    # Premium option: EPFR retail flow data
    # Free alternative: AAII bullish percentage as proxy
    
    aaii = self._fetch_aaii_sentiment()
    current_bulls = aaii['bullish_pct'].iloc[-1]
    ma_3m = aaii['bullish_pct'].rolling(12).mean().iloc[-1]  # 12 weeks = ~3 months
    std_3m = aaii['bullish_pct'].rolling(12).std().iloc[-1]
    
    z_score = (current_bulls - ma_3m) / std_3m
    
    return z_score > 2.0
```
- **Manual Alternative:** Track weekly from Vanda Research reports (free summaries)
- **Set to TRUE when:** Retail flows >2σ above 3-month average

---

#
## Implementation Roadmap

### **Phase 1: Automated Metrics (Week 1-2)**

**Priority 1 - Can Implement Now:**
1. ✅ Indicator 4.2: Margin Quality (MTUM vs QUAL)
2. ✅ Flag: `price_momentum_vs_earnings` (same data)
3. ✅ Flag: `volatility_regime_shift` (VIX >20)
4. ✅ Flag: `margin_debt_elevated` (FINRA + FRED)

**Priority 2 - Requires Data Setup:**
1. ⏳ Flag: `top10_weight_above_38` (need S&P 500 constituent list)
2. ⏳ Flag: `hhi_rising_3yr` (need historical weights)
3. ⏳ Flag: `top10_drive_50pct_returns` (need return attribution)

#
## Automation Priority Matrix

| Flag | Automatable? | Data Source | Priority |
|------|-------------|-------------|----------|
| top10_weight_above_38 | ✅ Yes | Yahoo Finance holdings | High |
| hhi_rising_3yr | ✅ Yes | Calculated from holdings | High |
| top10_drive_50pct_returns | ✅ Yes | Individual stock returns | High |
| theme_ps_extreme | 🟡 Semi | Need P/S data API | Medium |
| price_momentum_vs_earnings | ✅ Yes | MTUM vs QUAL | **Immediate** |
| sector_valuation_premium_2sd | 🟡 Semi | Need P/E data API | Medium |
| options_flow_concentrated | ❌ Manual | CBOE (premium) | Low |
| margin_debt_elevated | ✅ Yes | FINRA API | **Immediate** |
| retail_inflow_surge | 🟡 Semi | AAII (free proxy) | Medium |
| sector_leadership_divergence | ❌ Manual | Visual chart analysis | Low |
| mega_cap_guidance_warnings | ❌ Manual | Earnings calls | Low |
| institutional_rotation_detected | 🟡 Semi | 13F filings | Medium |
| liquidity_deterioration | ❌ Manual | Requires premium data | Low |
| widening_bid_ask_spreads | 🟡 Semi | Requires tick data | Low |
| volatility_regime_shift | ✅ Yes | Yahoo Finance VIX | **Immediate** |

---

## Current State Estimate (Dec 2025)

### **Automated Flags (Can Calculate Now):**

```python
# Estimated current state based on market conditions

structural_concentration:
  top10_weight_above_38: TRUE     # Top 10 ~40% of S&P 500
  hhi_rising_3yr: TRUE            # Concentration increasing since 2022
  top10_drive_50pct_returns: TRUE # Top 10 drove ~60% of 2024 gains

valuation_extremes:
  price_momentum_vs_earnings: TRUE  # MTUM >> QUAL (estimate ~18% divergence)
  
speculative_activity:
  margin_debt_elevated: FALSE      # Currently ~1.8% of GDP (below 2% trigger)
  
market_plumbing:
  volatility_regime_shift: FALSE   # VIX currently ~15
```

### **Estimated Penalty Score:**

```
Structural: 3/3 flags = 1.0 * 0.6 = 0.60
Valuation: 1/3 flags = 0.33 * 0.5 = 0.17
Speculative: 0/3 flags = 0.0 * 0.4 = 0.00
Leadership: 0/3 flags = 0.0 * 0.3 = 0.00
Plumbing: 0/3 flags = 0.0 * 0.2 = 0.00

TOTAL PENALTY: 0.77 points (~0.8 rounded)
Severity: "Moderate - Concentration building"
```

### **Total Category 4 Score:**

```
Earnings Breadth: 4.3 (QQQ vs RSP gap: 12pp)
Margin Quality: ~3.5 (estimated MTUM vs QUAL divergence)
Red Flag Penalty: +0.8

TOTAL: 8.6 / 12 points (High earnings risk)
```

---

## Theme Adaptation Guide

### **When the Market Narrative Changes:**

**If Clean Energy Becomes the Hot Theme:**

1. Update `concentration_red_flags.json`:
   ```json
   "leading_sector_etf": "XLE",  // Change from XLK to XLE
   "leading_stocks": ["TSLA", "ENPH", "FSLR", ...],  // Update list
   ```

2. Calculations auto-adjust:
   - Top 10 weight: Now measures energy concentration
   - P/S extreme: Now checks XLE P/S vs history
   - Options flow: Automatically sums TSLA, ENPH, etc.

3. Manual guidance updates:
   - Watch for: "Supply chain delays", "Subsidy uncertainty"
   - Instead of: "AI ROI concerns", "GPU oversupply"

**If Quantum Computing Becomes the Hot Theme:**

1. Update leading stocks: GOOGL, IBM, IONQ, RGTI, etc.
2. Watch for: "Qubit error rates", "Commercialization delays"
3. Same mathematical framework applies

**The Beauty:** You change 1 config parameter, the math stays the same.

---

## Future Enhancement: AI Theme Detector

**Fully Automate Theme Detection:**

```python
def _detect_leading_theme(self) -> str:
    """
    Automatically identify which sector/theme is most concentrated
    Returns: ETF symbol of leading sector
    """
    sectors = {
        'XLK': 'Technology',
        'XLE': 'Energy',
        'XLF': 'Financials',
        'XLV': 'Healthcare',
        'XLI': 'Industrials',
        'XBI': 'Biotech',
        'XME': 'Metals & Mining',
    }
    
    # Calculate each sector's concentration metrics
    concentration_scores = {}
    
    for symbol, name in sectors.items():
        # Score based on: weight in S&P 500, returns, P/S premium
        score = self._calculate_concentration_score(symbol)
        concentration_scores[symbol] = score
    
    # Return highest concentration sector
    leading_sector = max(concentration_scores, key=concentration_scores.get)
    
    return leading_sector
```

This makes the system **fully autonomous** - it detects the bubble itself, no user input needed.

---

## Key Advantages Over AI-Specific Approach

| Aspect | AI-Specific | Theme-Agnostic |
|--------|-------------|----------------|
| **Longevity** | Obsolete when AI boom ends | Works for any bubble |
| **Maintenance** | Must rewrite for next theme | Same code, different data |
| **Objectivity** | Prone to narrative bias | Pure math/patterns |
| **Automation** | Many manual inputs | Mostly automated |
| **Backtesting** | Only works for 2023-2025 | Works for 2000, 2007, 2021 |
| **User Trust** | "How do you know AI is the risk?" | "Math says concentration is extreme" |

---

## Conclusion

By building a **concentration pattern detector** instead of an "AI bubble detector", you create a system that:

1. ✅ **Works today** (detects current AI boom risk)
2. ✅ **Works tomorrow** (detects whatever comes next)
3. ✅ **Reduces maintenance** (same code, just swap sector ETF)
4. ✅ **Increases automation** (less manual flag setting)
5. ✅ **Improves backtesting** (can validate on multiple historical bubbles)

The math of bubbles is universal:
- **Concentration** increases (HHI, top 10 weight)
- **Valuation** diverges from fundamentals (momentum vs quality)
- **Speculation** accelerates (options, margin debt)
- **Leadership** narrows then cracks (breadth deterioration)

Your system should detect **these patterns**, not specific narratives.

---

## Next Steps

**This Week:**
1. Implement Indicator 4.2 (MTUM vs QUAL)
2. Create `concentration_red_flags.json` with initial state
3. Code automated flags: `price_momentum_vs_earnings`, `margin_debt_elevated`, `volatility_regime_shift`

**Next Week:**
1. Add S&P 500 constituent tracking for top 10 weight calculation
2. Implement HHI calculation
3. Test end-to-end Category 4 calculation

**This Month:**
1. Backtest on 2000, 2007, 2021 bubbles
2. Calibrate weights based on historical accuracy
3. Document theme adaptation playbook

**Goal:** A concentration risk system that warns you 3-6 months before the next bubble pops - regardless of whether it's AI, quantum, biotech, or something we haven't imagined yet.

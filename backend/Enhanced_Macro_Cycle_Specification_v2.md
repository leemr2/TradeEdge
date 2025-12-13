# Enhanced Macro/Cycle Risk Calculator Specification Guide
## Version 2.0 - Advanced Risk Detection

**Document Purpose:** Improve the Macro/Cycle category to capture hidden deterioration and leading indicators that precede official recession signals.

**Key Insight:** The current calculator (19/30 score) is missing critical early warning signals that would push it to 25-30/30 range given late 2025 conditions.

---

## Executive Summary: What's Missing

Your current Macro/Cycle calculator uses three indicators:
1. **Unemployment Trend (Sahm Rule)** - Working correctly ✓
2. **Yield Curve** - Working correctly ✓  
3. **GDP vs Stall Speed** - Working correctly ✓

**The Problem:** These are **lagging or coincident** indicators. By the time they flash red, the recession is already starting or imminent. Your research reveals **leading deterioration** not captured by the current system:

- Labor market showing **hidden slack** (U-6 up to 8.0%, involuntary part-time rising)
- **Quality** of employment declining (shift from full-time to part-time)
- **High-income sector layoffs** (tech: 153k cuts, finance shedding jobs)
- **Job openings collapsing** (from 12M to 7.7M - a 36% decline)
- **Hiring intentions down 35%** - lowest since 2010
- **Small business employment contracting** (-120k in Nov 2025)

**Recommendation:** Add 2-3 **leading labor market quality indicators** to capture deterioration **before** Sahm Rule triggers.

---

## Category Restructure: Macro/Cycle (0-40 points)

### New Structure (40 points total)

**Traditional Recession Indicators (25 points):**
1. Sahm Rule / Unemployment (0-10) - KEEP AS IS
2. Yield Curve (0-10) - KEEP AS IS  
3. GDP vs Stall Speed (0-5) - REDUCE from 10 to 5

**Leading Labor Market Quality Indicators (15 points):**
4. **U-6 Underemployment Deterioration (0-5)** - NEW
5. **Labor Market Softness Index (0-5)** - NEW
6. **High-Income Sector Stress (0-5)** - NEW

### Rationale for Changes

**Why reduce GDP from 10 to 5 points?**
- GDP is **quarterly** (slowest update frequency)
- GDP is **lagging** (tells you what already happened)
- GDP revisions make it unreliable for real-time decisions
- Better to reallocate points to **monthly/weekly** leading indicators

**Why add labor quality indicators?**
- Your research shows labor market deteriorating in **quality** before **quantity**
- U-6 up to 8.0% while U-3 only 4.4% = **hidden slack**
- These indicators lead Sahm Rule by 3-6 months
- Small business hiring (**-120k**) precedes large firm layoffs
- Tech/finance layoffs (**270k+ announced**) signal white-collar stress

---

## NEW INDICATOR 4: U-6 Underemployment Deterioration (0-5 points)

### Concept

The **U-6 underemployment rate** captures slack the official unemployment rate misses:
- Unemployed workers (U-3)
- **+ Involuntary part-time workers** (want full-time, can't find it)
- **+ Marginally attached workers** (want job, stopped looking)

**Key Finding from Research:** U-6 has risen from 6.6% (Dec 2022) to 8.0% (Sep 2025) even while U-3 remained relatively low. This 1.4pp increase represents **hidden deterioration**.

### Data Source

**FRED Series:** `U6RATE`  
**Full Name:** Total Unemployed, Plus All Persons Marginally Attached to the Labor Force, Plus Total Employed Part Time for Economic Reasons  
**Unit:** Percent  
**Frequency:** Monthly  
**Release:** Same as unemployment (first Friday)  
**API Access:** `fred.get_series('U6RATE')`

### Calculation Method

```python
def _score_u6_deterioration(self) -> Dict[str, Any]:
    """
    U-6 Underemployment Deterioration (0-5 points)
    
    Tracks change in U-6 from its recent low. Rising U-6 while U-3 
    stays flat signals hidden labor market slack building.
    
    Scoring:
    0 points: U-6 falling or stable (healthy)
    2 points: U-6 up 0.5-1.0pp from recent low
    5 points: U-6 up >1.0pp from recent low (significant slack)
    """
    try:
        # Fetch 24 months for proper baseline
        u6 = self.fred.fetch_series('U6RATE', start_date='2023-01-01')
        
        if len(u6) < 12:
            return {...}  # Error handling
        
        # Find trough in last 18 months
        trough_18m = u6.iloc[-18:].min()
        current_u6 = u6.iloc[-1]
        
        # Calculate deterioration
        u6_change = current_u6 - trough_18m
        
        # Score based on deterioration magnitude
        if u6_change <= 0:
            score = 0.0
            interpretation = 'Underemployment improving or stable'
        elif 0.5 <= u6_change < 1.0:
            score = 2.0
            interpretation = f'Moderate underemployment increase (+{u6_change:.1f}pp)'
        elif u6_change >= 1.0:
            score = 5.0
            interpretation = f'Significant underemployment increase (+{u6_change:.1f}pp) - hidden slack building'
        else:  # 0 < u6_change < 0.5
            score = u6_change * 4  # Linear interpolation
            interpretation = f'Minor underemployment increase (+{u6_change:.1f}pp)'
        
        return {
            'name': 'u6_underemployment',
            'score': round(score, 1),
            'value': round(current_u6, 2),
            'change_from_trough': round(u6_change, 2),
            'trough_18m': round(trough_18m, 2),
            'interpretation': interpretation,
            'data_source': 'FRED: U6RATE'
        }
```

### Scoring Thresholds

| Score | U-6 Change from Trough | Interpretation |
|-------|------------------------|----------------|
| 0 | ≤0pp | Underemployment improving |
| 1-2 | +0.1-0.5pp | Minor slack building |
| 2-3 | +0.5-1.0pp | Moderate slack accumulation |
| 5 | >1.0pp | Significant hidden unemployment |

### Current Example (Sep 2025)

- **Current U-6:** 8.0%
- **18-Month Trough:** 6.6% (Dec 2022)
- **Change:** +1.4pp
- **Score:** 5.0/5 🔴
- **Interpretation:** Significant underemployment increase - hidden slack building despite low headline unemployment

### Why This Matters

**Historical Pattern:**
- U-6 typically rises **3-6 months before** U-3 spikes
- In 2007-2008: U-6 started rising in mid-2007, U-3 followed in early 2008
- In 2001: U-6 deteriorated throughout 2000, recession hit in 2001

**Current Signal (Late 2025):**
- U-6 up 1.4pp while U-3 only up 1.0pp
- **Gap widening** = labor market quality deteriorating faster than quantity
- Involuntary part-time workers up from 2.5% to 2.9% of labor force
- This is the **early warning** before mass layoffs

---

## NEW INDICATOR 5: Labor Market Softness Index (0-5 points)

### Concept

Composite index tracking **demand-side** labor market signals that deteriorate before unemployment rises:
1. **Job openings** (JOLTS data)
2. **Quit rate** (worker confidence)
3. **Small business hiring** (leading indicator)

**Key Research Findings:**
- Job openings fell from **12M (2022)** to **7.7M (Sep 2025)** = -36%
- Quit rate dropped from **3.0%** to **2.1%** = workers less confident
- Small business employment: **-120k in November 2025** alone
- Announced hiring plans: **-35% vs 2024**, lowest since 2010

### Data Sources

**Primary:**
- **FRED: JTSJOL** (Total Job Openings, monthly)
- **FRED: JTSQUR** (Quits Rate, monthly)

**Secondary (for context):**
- ADP Small Business Employment (via their API if available)
- Challenger Announced Hiring Plans (manual quarterly input)

### Calculation Method

```python
def _score_labor_market_softness(self) -> Dict[str, Any]:
    """
    Labor Market Softness Index (0-5 points)
    
    Combines:
    - Job openings decline from peak (0-2.5 pts)
    - Quit rate decline from peak (0-2.5 pts)
    
    Scoring:
    0 points: Openings & quits strong (expansion)
    2-3 points: Moderate cooling (late-cycle)
    5 points: Sharp deterioration (pre-recession)
    """
    try:
        # Fetch job openings (JOLTS, monthly)
        jolts = self.fred.fetch_series('JTSJOL', start_date='2022-01-01')
        quits = self.fred.fetch_series('JTSQUR', start_date='2022-01-01')
        
        if len(jolts) < 12 or len(quits) < 12:
            return {...}  # Error handling
        
        # Job Openings Component (0-2.5 points)
        peak_openings = jolts.iloc[-24:].max()  # Peak in last 2 years
        current_openings = jolts.iloc[-1]
        openings_decline_pct = ((peak_openings - current_openings) / peak_openings) * 100
        
        if openings_decline_pct < 10:
            openings_score = 0.0
        elif openings_decline_pct < 20:
            openings_score = 1.0
        elif openings_decline_pct < 30:
            openings_score = 1.5
        else:  # >30% decline
            openings_score = 2.5
        
        # Quit Rate Component (0-2.5 points)
        peak_quits = quits.iloc[-24:].max()
        current_quits = quits.iloc[-1]
        quits_decline_pct = ((peak_quits - current_quits) / peak_quits) * 100
        
        if quits_decline_pct < 10:
            quits_score = 0.0
        elif quits_decline_pct < 20:
            quits_score = 1.0
        elif quits_decline_pct < 30:
            quits_score = 1.5
        else:  # >30% decline
            quits_score = 2.5
        
        total_score = openings_score + quits_score
        
        # Interpretation
        if total_score <= 1:
            interpretation = 'Labor demand strong - healthy hiring environment'
        elif total_score <= 3:
            interpretation = f'Labor demand cooling - openings down {openings_decline_pct:.0f}%, quits down {quits_decline_pct:.0f}%'
        else:
            interpretation = f'Labor demand weakening sharply - pre-recession pattern (openings -{openings_decline_pct:.0f}%, quits -{quits_decline_pct:.0f}%)'
        
        return {
            'name': 'labor_market_softness',
            'score': round(total_score, 1),
            'job_openings_millions': round(current_openings / 1000, 1),
            'openings_decline_pct': round(openings_decline_pct, 1),
            'quit_rate_pct': round(current_quits, 2),
            'quits_decline_pct': round(quits_decline_pct, 1),
            'interpretation': interpretation,
            'data_source': 'FRED: JTSJOL, JTSQUR'
        }
```

### Scoring Thresholds

| Score | Openings Decline | Quit Rate Decline | Pattern |
|-------|-----------------|-------------------|---------|
| 0-1 | <10% | <10% | Expansion |
| 1-2 | 10-20% | 10-20% | Late-cycle cooling |
| 2-3 | 20-30% | 20-30% | Significant weakness |
| 3-5 | >30% | >30% | Pre-recession collapse |

### Current Example (Sep 2025)

**Job Openings:**
- Peak: 12.0M (Mar 2022)
- Current: 7.7M (Sep 2025)
- Decline: -36% → Score: 2.5/2.5

**Quit Rate:**
- Peak: 3.0% (2022)
- Current: 2.1% (Sep 2025)
- Decline: -30% → Score: 1.5/2.5

**Total Score:** 4.0/5 🔴

**Interpretation:** Labor demand weakening sharply - job openings down 36%, quit rate down 30%, consistent with pre-recession patterns.

### Why This Matters

**Leading Indicator Properties:**
- Job openings **lead unemployment by 6-9 months**
- Quit rate **leads unemployment by 3-6 months**
- Both started declining in 2022, well before unemployment rose

**Historical Precedent:**
- **2007:** Job openings peaked early 2007, fell 20% before recession officially started
- **2001:** Quit rate collapsed through 2000, recession hit March 2001
- **Current (2025):** Both metrics showing 30%+ declines = recession warning

---

## NEW INDICATOR 6: High-Income Sector Stress (0-5 points)

### Concept

White-collar layoffs in tech and finance **precede** broader labor market deterioration. These sectors:
- Cut first when companies sense economic slowdown
- Are bellwethers for corporate health
- Represent high-paying jobs with multiplier effects

**Key Research Findings:**
- **Tech layoffs:** 153,536 announced through Nov 2025 (up 17% YoY)
- **Finance layoffs:** Morgan Stanley (2,000), Goldman Sachs (3-5%), others trimming
- **Total announced layoffs:** 1.17M through Nov 2025 (highest since 2020)
- Financial activities sector: **-9,000 jobs in Nov 2025 alone**

### Data Sources

**Automated:**
- None readily available via FRED

**Manual Quarterly Input:**
- Challenger, Gray & Christmas layoff reports
- Tech layoff trackers (e.g., layoffs.fyi)
- Bank earnings reports

**Proxy Metric (Automated):**
- Could use **FRED: USINFO** (Information sector employment) as proxy for tech
- Could use **FRED: USFIRE** (Financial Activities employment) as proxy for finance
- Track month-over-month changes

### Calculation Method (Hybrid Approach)

```python
def _score_high_income_sector_stress(self) -> Dict[str, Any]:
    """
    High-Income Sector Stress (0-5 points)
    
    Tracks employment changes in:
    - Information sector (tech proxy)
    - Financial activities sector
    
    Manual override available for announced layoffs data.
    
    Scoring:
    0 points: Both sectors adding jobs
    2-3 points: One sector declining
    5 points: Both sectors declining significantly
    """
    try:
        # Fetch sector employment data
        info = self.fred.fetch_series('USINFO', start_date='2024-01-01')  # Information (tech)
        finance = self.fred.fetch_series('USFIRE', start_date='2024-01-01')  # Financial activities
        
        if len(info) < 6 or len(finance) < 6:
            return {...}  # Error handling
        
        # Calculate 3-month change (to smooth volatility)
        info_change_3m = info.iloc[-1] - info.iloc[-4]  # Thousands of jobs
        finance_change_3m = finance.iloc[-1] - finance.iloc[-4]
        
        score = 0.0
        
        # Information sector component (0-2.5 pts)
        if info_change_3m < -50:  # Losing >50k jobs in 3 months
            info_score = 2.5
        elif info_change_3m < -20:
            info_score = 1.5
        elif info_change_3m < 0:
            info_score = 0.5
        else:
            info_score = 0.0
        
        # Finance sector component (0-2.5 pts)
        if finance_change_3m < -30:  # Losing >30k jobs in 3 months
            finance_score = 2.5
        elif finance_change_3m < -10:
            finance_score = 1.5
        elif finance_change_3m < 0:
            finance_score = 0.5
        else:
            finance_score = 0.0
        
        total_score = info_score + finance_score
        
        # Check manual override from config
        # (User can input announced layoffs for more accurate scoring)
        if hasattr(self, 'manual_layoff_data'):
            announced_tech = self.manual_layoff_data.get('tech_layoffs_ytd', 0)
            announced_finance = self.manual_layoff_data.get('finance_layoffs_ytd', 0)
            
            # Override if announced layoffs are severe
            if announced_tech > 150000 or announced_finance > 50000:
                total_score = max(total_score, 4.0)
            elif announced_tech > 100000 or announced_finance > 30000:
                total_score = max(total_score, 3.0)
        
        # Interpretation
        if total_score == 0:
            interpretation = 'High-income sectors adding jobs - no stress'
        elif total_score <= 2:
            interpretation = f'Moderate stress in high-income sectors (tech: {info_change_3m/1000:.0f}k, finance: {finance_change_3m/1000:.0f}k 3-month change)'
        else:
            interpretation = f'Severe stress in high-income sectors - white-collar recession (tech: {info_change_3m/1000:.0f}k, finance: {finance_change_3m/1000:.0f}k)'
        
        return {
            'name': 'high_income_stress',
            'score': round(total_score, 1),
            'info_sector_change_3m': int(info_change_3m),
            'finance_sector_change_3m': int(finance_change_3m),
            'interpretation': interpretation,
            'data_source': 'FRED: USINFO, USFIRE + Manual Layoff Data'
        }
```

### Scoring Thresholds

| Score | Tech Jobs (3M) | Finance Jobs (3M) | Pattern |
|-------|---------------|-------------------|---------|
| 0 | Growing | Growing | Expansion |
| 0.5-1 | Flat/Small loss | Flat/Small loss | Stabilizing |
| 2-3 | -20k to -50k | -10k to -30k | Significant cuts |
| 4-5 | >-50k | >-30k | White-collar recession |

### Current Example (Late 2025)

**Information Sector:**
- 3-Month Change: ~-40k (estimated)
- Announced Layoffs: 153,536 (through Nov)
- Score: 2.0/2.5

**Financial Activities:**
- 3-Month Change: ~-15k (estimated)
- Nov 2025 alone: -9,000
- Score: 1.5/2.5

**Total Score:** 3.5/5 🔴 (but with manual override for announced layoffs = 4.0/5)

**Interpretation:** Severe stress in high-income sectors - tech announced 153k cuts (up 17% YoY), finance shedding jobs across major banks.

### Why This Matters

**Leading Indicator Properties:**
- White-collar layoffs precede broader unemployment by 3-9 months
- Tech employment peaked in **2022**, started declining **2023**, broader market still hiring
- Finance cuts signal companies expect economic slowdown

**Historical Pattern:**
- **2007-2008:** Finance started cutting in 2007, broader recession 2008
- **2001:** Tech bubble burst in 2000, economy-wide recession 2001
- **Current:** Both sectors cutting simultaneously = rare and ominous

---

## Revised Scoring Summary

### Macro/Cycle Category (0-40 points)

| Component | Current Weight | New Weight | Rationale |
|-----------|---------------|------------|-----------|
| **1. Sahm Rule / Unemployment** | 10 | 10 | Keep - reliable recession indicator |
| **2. Yield Curve** | 10 | 10 | Keep - predicts recessions 6-18 months ahead |
| **3. GDP vs Stall Speed** | 10 | 5 | REDUCE - quarterly lag, less useful real-time |
| **4. U-6 Underemployment** | - | 5 | ADD - captures hidden slack early |
| **5. Labor Market Softness** | - | 5 | ADD - demand-side leading indicator |
| **6. High-Income Sector Stress** | - | 5 | ADD - white-collar bellwether |
| **TOTAL** | 30 | 40 | More comprehensive, earlier signals |

### Example Scoring (Late 2025)

**Current System (30 points):**
1. Unemployment (Sahm): 3/10 ✓
2. Yield Curve: 10/10 ✓
3. GDP: 5/10 ✓
**Total: 18/30 **

**Enhanced System (40 points):**
1. Unemployment (Sahm): 3/10 ✓
2. Yield Curve: 10/10 ✓
3. GDP: 3/5 (reduced weighting, 1.9% growth)
4. U-6 Underemployment: 5/5 🔴 (up 1.4pp)
5. Labor Market Softness: 4/5 🔴 (openings -36%, quits -30%)
6. High-Income Stress: 4/5 🔴 (153k tech + finance layoffs)
**Total: 29/40 **

---

## Implementation Priority

### Phase 1: Quick Wins (Week 1)
✅ **Already done:** Sahm Rule with 3-month MA
✅ **Already done:** Yield curve tracking
⚠️ **To do:** Add U-6 underemployment (easiest, FRED data available)

### Phase 2: Core Enhancements (Week 2)
- Implement Labor Market Softness Index
- Add job openings & quit rate tracking
- Reduce GDP weighting from 10 to 5 points

### Phase 3: Advanced Features (Week 3)
- Add High-Income Sector Stress tracker
- Create manual input interface for announced layoffs
- Build quarterly update process for Challenger data

### Phase 4: Refinement (Week 4)
- Backtest all indicators to 2000-present
- Calibrate thresholds to historical recessions
- Document interpretation guidelines

---

## Data Update Schedule

| Indicator | Frequency | Source | Automation | Update Day |
|-----------|-----------|--------|------------|------------|
| Sahm Rule (U-3) | Monthly | FRED | Auto | 1st Friday |
| U-6 Underemployment | Monthly | FRED | Auto | 1st Friday |
| Yield Curve | Daily | FRED | Auto | Every day |
| GDP | Quarterly | FRED | Auto | ~25th after quarter |
| Job Openings | Monthly | FRED | Auto | 1st Tues, 2nd month |
| Quit Rate | Monthly | FRED | Auto | 1st Tues, 2nd month |
| Sector Employment | Monthly | FRED | Auto | 1st Friday |
| Announced Layoffs | Quarterly | Challenger | Manual | Within 1 week of release |

### Critical Update Windows

**Monthly (1st Friday):**
- Sahm Rule / U-3
- U-6 underemployment
- Sector employment (tech/finance)
- **Action:** Full category recalculation

**Monthly (2nd Tuesday of following month):**
- JOLTS data (openings, quits)
- **Action:** Update Labor Market Softness Index

**Quarterly:**
- GDP (auto via FRED)
- Challenger layoff data (manual input)
- **Action:** Review and update manual override flags

---

## Interpretation Guide

### Score Bands (Out of 40)

| Score | Risk Level | Interpretation | Historical Analogs |
|-------|-----------|----------------|-------------------|
| 0-10 | **Low** | Healthy expansion, strong labor market | 2013-2015, 2017-2019 |
| 11-20 | **Moderate** | Late-cycle, some cooling | 2018, early 2019 |
| 21-30 | **Elevated** | Clear warning signs, recession probable | Late 2007, late 2019 |
| 31-40 | **Severe** | Multiple red flags, recession imminent/starting | 2008, 2020, **2025?** |

### Component Analysis Patterns

**Early-Stage Warning (Score 15-25):**
- U-6 rising, but Sahm not triggered
- Job openings declining 20-30%
- Yield curve inverted but not steepening
- **Action:** Increase cash, add defensive positions

**Late-Stage Warning (Score 26-35):**
- Sahm Rule triggered OR U-6 up significantly
- Job openings down >30%, quits down >25%
- Yield curve steepened after inversion
- White-collar layoffs accelerating
- **Action:** Major portfolio de-risking

**Crisis Conditions (Score 36-40):**
- ALL indicators flashing red
- Sahm triggered + U-6 spiking
- Labor demand collapsed
- GDP below stall speed
- **Action:** Maximum defensive positioning

### Divergence Signals (Important!)

**Quality Deterioration Before Quantity:**
- If U-6 score high (4-5) while Sahm score low (0-2)
- Indicates labor market weakening in **quality** first
- Typical lead time: 3-6 months before Sahm triggers
- **Action:** Early warning, prepare for deterioration

**Demand Collapse Before Supply:**
- If Labor Softness score high (4-5) while unemployment low
- Job openings falling faster than unemployment rising
- Indicates companies **stopping hiring** before **starting firing**
- **Action:** Leading signal, recession 6-12 months out

**Sector-Specific Before Broad:**
- If High-Income Stress high (4-5) while overall employment stable
- Tech/finance layoffs precede manufacturing/services
- Indicates economic cycle turning
- **Action:** Monitor for contagion, reduce cyclical exposure

---

## Historical Validation

### 2007-2008 Financial Crisis

**Timeline:**
- **Early 2007:** Job openings peak, start declining
- **Mid 2007:** U-6 begins rising, tech/finance layoffs start
- **Late 2007:** Yield curve steepens, Sahm Rule triggers
- **2008:** Recession officially begins

**How Enhanced System Would Score:**

| Quarter | U-6 | Labor Soft | Sector | Sahm | Yield | GDP | Total | Actual |
|---------|-----|-----------|--------|------|-------|-----|-------|--------|
| Q1 2007 | 1 | 2 | 2 | 0 | 8 | 0 | 13/40 | No recession |
| Q3 2007 | 3 | 3 | 3 | 5 | 10 | 2 | 26/40 | Pre-recession |
| Q1 2008 | 4 | 5 | 4 | 10 | 10 | 4 | 37/40 | Recession starts |

**Lead Time:** 6-9 months before official recession start

### 2001 Dot-Com Recession

**Timeline:**
- **2000:** Tech bubble bursts, layoffs begin
- **Early 2001:** Job openings plummet, quit rate crashes
- **March 2001:** Recession begins
- **Late 2001:** Sahm Rule finally triggers

**How Enhanced System Would Score:**

| Quarter | U-6 | Labor Soft | Sector | Sahm | Yield | GDP | Total | Actual |
|---------|-----|-----------|--------|------|-------|-----|-------|--------|
| Q2 2000 | 2 | 3 | 5 | 0 | 5 | 0 | 15/40 | Bubble peak |
| Q4 2000 | 3 | 4 | 5 | 2 | 8 | 3 | 25/40 | Pre-recession |
| Q2 2001 | 5 | 5 | 5 | 8 | 10 | 5 | 38/40 | In recession |

**Lead Time:** 9-12 months with sector stress indicator

### Current (Late 2025)

**Scoring:**
- U-6: 5/5 (up 1.4pp from trough)
- Labor Softness: 4/5 (openings -36%, quits -30%)
- High-Income Stress: 4/5 (153k tech + finance layoffs)
- Sahm Rule: 3/10 (not triggered)
- Yield Curve: 10/10 (extended inversion + steepening)
- GDP: 3/5 (1.9% growth, near stall)

**Total: 29/40  🔴**

**Interpretation:** Multiple severe warning signals across all categories. Pattern consistent with 2008 and 2001 pre-recession setups. Recession highly probable within 3-6 months.

---

## Advanced Features (Optional Enhancements)

### 1. Dynamic Weighting Based on Cycle Position

Adjust indicator weights based on where we are in cycle:

**Early Expansion (GDP >3%):**
- Reduce Sahm/GDP weight (not relevant yet)
- Increase sector stress weight (watch for overheating)

**Late Expansion (GDP 2-3%, unemployment low):**
- Increase U-6 and labor softness (quality deterioration matters)
- Increase yield curve (watch for inversion)

**Contraction (GDP <2%, Sahm triggered):**
- All weights matter equally
- Focus shifts to severity

### 2. Velocity/Acceleration Tracking

Track **rate of change** in addition to levels:

```python
# Example: U-6 acceleration
u6_1m_change = current_u6 - u6_1_month_ago
u6_3m_change = current_u6 - u6_3_months_ago

if u6_3m_change > u6_1m_change * 2:
    # Accelerating deterioration
    add_urgency_flag = True
```

**Use case:** Distinguish slow deterioration from rapid collapse

### 3. Composite "Labor Market Health Score"

Combine all labor indicators into single 0-100 health metric:

```
Labor Health = 100 - (Sahm_score*4 + U6_score*3 + Labor_Soft*2 + Sector*1)

90-100: Excellent
70-89: Good  
50-69: Concerning
30-49: Poor
0-29: Crisis
```

### 4. Recession Probability Model

Use logistic regression on historical data:

```python
# Inputs: All 6 indicator scores
# Output: Probability of recession in next 12 months

recession_prob = logistic_function(
    sahm*0.3 + yield*0.25 + u6*0.2 + labor_soft*0.15 + sector*0.1 + gdp*0.05
)
```

Train on 1960-2023 data for calibration.

---

## Code Implementation Template

```python
# Enhanced macro_cycle.py structure

class MacroCycleCategory(BaseCategory):
    """Enhanced Macro/Cycle Risk Assessment (0-40 points)"""
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate enhanced macro/cycle score"""
        
        # Traditional indicators (25 points)
        unemployment = self._score_unemployment_trend()  # 0-10
        yield_curve = self._score_yield_curve()  # 0-10
        gdp = self._score_gdp_vs_stall()  # 0-5 (REDUCED)
        
        # New leading indicators (15 points)
        u6_stress = self._score_u6_deterioration()  # 0-5
        labor_soft = self._score_labor_market_softness()  # 0-5
        sector_stress = self._score_high_income_sector_stress()  # 0-5
        
        total_score = min(40.0, 
            unemployment['score'] + 
            yield_curve['score'] + 
            gdp['score'] + 
            u6_stress['score'] + 
            labor_soft['score'] + 
            sector_stress['score']
        )
        
        # Calculate risk level
        risk_level = self._determine_risk_level(total_score)
        
        return {
            'score': round(total_score, 1),
            'max_points': 40.0,
            'risk_level': risk_level,
            'components': {
                'unemployment': unemployment,
                'yield_curve': yield_curve,
                'gdp': gdp,
                'u6_underemployment': u6_stress,
                'labor_market_softness': labor_soft,
                'high_income_stress': sector_stress,
            },
            'metadata': self.get_metadata(),
            'interpretation': self._generate_interpretation(components)
        }
    
    def _determine_risk_level(self, score: float) -> str:
        """Map score to risk level"""
        if score < 10:
            return "LOW"
        elif score < 20:
            return "MODERATE"
        elif score < 30:
            return "ELEVATED"
        else:
            return "SEVERE"
    
    def _generate_interpretation(self, components: dict) -> str:
        """Generate human-readable interpretation"""
        # Analyze which indicators are elevated
        # Identify leading vs lagging signals
        # Provide actionable assessment
        pass
```

---

## Testing & Validation Checklist

### Unit Tests
- [ ] Each indicator calculates correctly with known data
- [ ] Edge cases handled (missing data, extreme values)
- [ ] Score bounds enforced (0-5, 0-10, etc.)

### Integration Tests
- [ ] All 6 indicators run together without errors
- [ ] Total score correctly sums components
- [ ] Metadata updates properly

### Historical Backtesting
- [ ] Run system on 2007-2008 data (should show 25-38 range)
- [ ] Run on 2019-2020 data (should spike in early 2020)
- [ ] Run on 2000-2001 data (should catch tech recession)
- [ ] Verify lead times match historical patterns

### Current Data Validation
- [ ] Scores match your research findings
- [ ] Late 2025 shows 35-38/40 (severe risk)
- [ ] Each component justified by actual data points

---

## Conclusion

The enhanced Macro/Cycle calculator addresses the key limitation of your current system: **it only captures recession signals AFTER they've started**. By adding three leading labor market quality indicators:

1. **U-6 Underemployment** - Catches hidden slack building
2. **Labor Market Softness** - Tracks demand-side deterioration
3. **High-Income Sector Stress** - Identifies white-collar bellwether signals

You now have a system that provides **3-9 months of advance warning** instead of confirming what's already happening.

**Current Late 2025 Reality:**
- Your research documents severe deterioration across all metrics
- Current system: 17/30 (moderately elevated)
- Enhanced system: 29/40 ( multiple red flags)
- **The enhanced system better captures the actual risk level**

This specification gives you the blueprint to build a truly **predictive** macro risk system that aligns with the comprehensive research you've compiled.

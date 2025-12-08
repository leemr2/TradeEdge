# Product Requirements Document (PRD)
## TradeEdge: AI-Powered Investment Command Center

**Version:** 2.0  
**Author:** Mark  
**Date:** December 2025  
**Status:** Draft

---

## Executive Summary

TradeEdge is a personal investment tool designed to give retail investors the analytical capabilities typically reserved for institutional players. Rather than relying on brokers or advisors whose interests may not always align with yours, TradeEdge provides proactive insights, risk monitoring, and AI-augmented research to support sound, independent investment decisions.

The system integrates your existing Google Trends volatility predictor with comprehensive market monitoring, stock screening, portfolio management, and LLM-powered analysis—combining a **chat-first interface** with **modular Python analytics** to transform you from a reactive trader into a proactive market participant.

---

## Problem Statement

**The Retail Investor Disadvantage**

Retail investors face a fundamental information and tools asymmetry:

1. **Dependency on Intermediaries**: Brokers and advisors may have misaligned incentives (commissions, proprietary products, limited research depth)
2. **Reactive Positioning**: Most retail tools show what happened, not what's likely to happen
3. **Information Fragmentation**: Market data, news, fundamentals, and sentiment exist in silos requiring manual synthesis
4. **Analysis Paralysis**: Too much raw data, too little actionable insight
5. **Emotional Decision-Making**: No systematic framework to counter fear/greed cycles

**Target User**

A self-directed retail investor who:
- Has intermediate market knowledge and wants to grow expertise
- Currently uses basic brokerage tools and free resources
- Wants to make informed decisions independently
- Has 2-5 hours/week to dedicate to portfolio management
- Manages a portfolio in the $10K-$500K range

---

## Product Vision

**Transform retail investors from reactive traders into proactive, data-informed market participants through AI-augmented analysis and predictive monitoring.**

### Design Philosophy

Think of TradeEdge as three integrated layers:
1. **Weather Forecast** (Macro Regime) — What kind of market environment are we in?
2. **Terrain Map** (Opportunity Identification) — What's worth buying or selling?
3. **GPS Navigation** (Risk Management) — How should I position and when to hedge?

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      ELECTRON SHELL                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              NEXT.JS FRONTEND                             │  │
│  │   - Dashboard UI (3-screen layout)                        │  │
│  │   - Chat Interface (primary interaction)                  │  │
│  │   - Data Visualizations                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↕                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           AGENT ORCHESTRATOR (Node.js)                    │  │
│  │   - Routes tasks to specialized agents                    │  │
│  │   - Manages conversation context                          │  │
│  │   - Coordinates multi-agent workflows                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↕                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           PYTHON ANALYTICS ENGINE                         │  │
│  │   - Standalone modular scripts ("brains")                 │  │
│  │   - Each independently testable                           │  │
│  │   - Simple HTTP API wrapper (FastAPI)                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↕                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              LOCAL DATA LAYER                             │  │
│  │   - SQLite (structured data)                              │  │
│  │   - JSON files (configs, cache)                           │  │
│  │   - Vector DB (embeddings, memory)                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Design Principles

1. **Modular Python Scripts ("Brains")**: Each analytics module is a pure function—takes input, returns output. No shared state. No dependencies on other scripts.

2. **Agent-Based Architecture**: Specialized AI agents route queries, coordinate research, and synthesize insights using Claude API.

3. **Chat-First Interface**: Natural language is the primary interaction mode, with traditional dashboards as visual supplements.

4. **Local-First Data**: All data stored locally (SQLite, JSON, Vector DB) for privacy and speed.

---

## Python Analytics Modules

### Module Structure

Each Python script is an independent "brain" that can be:
- Run from command line for testing
- Called via HTTP API from the frontend
- Composed by agents for complex workflows

```
backend/analytics/
├── core/
│   ├── cmds_calculator.py          # Combined Market Danger Score
│   ├── frs_calculator.py           # Fundamental Risk Score
│   ├── volatility_predictor.py     # Google Trends model (your existing work)
│   ├── market_internals.py         # Breadth, concentration metrics
│   └── valuation_metrics.py        # P/E, Buffett indicator, equity yield
├── screening/
│   ├── value_quality_momentum.py   # VQM scanner
│   ├── boring_business.py          # Unsexy industry filter
│   ├── turnaround_detector.py      # Recovery opportunities
│   └── insider_tracker.py          # Management buying signals
├── risk/
│   ├── treasury_stress.py          # Bond market health
│   ├── credit_monitor.py           # HY spreads, CRE stress
│   ├── position_sizer.py           # Kelly criterion calculator
│   └── correlation_tracker.py      # Portfolio correlations
├── technical/
│   ├── trend_analyzer.py           # Multi-timeframe analysis
│   ├── support_resistance.py       # Key price levels
│   └── volume_profile.py           # Unusual activity detection
└── data_fetchers/
    ├── fred_client.py              # Economic data (FRED API)
    ├── yfinance_client.py          # Market data (Yahoo Finance)
    ├── pytrends_client.py          # Google Trends data
    └── sentiment_aggregator.py     # News, social sentiment
```

### Key Design Rules for Scripts

1. **Each script has a `main()` function** callable from CLI
2. **Outputs JSON to stdout** for easy testing and integration
3. **HTTP API is just a thin wrapper** calling these scripts
4. **Scripts cache their own data locally** (JSON files)
5. **No script depends on another script running first**

### Example Interface

```bash
# Test individual script
python backend/analytics/core/cmds_calculator.py
# Output: {"cmds": 82, "frs": 87, "vp": 72, "zone": "EXTREME"}

# Run screening with parameters
python backend/analytics/screening/boring_business.py --min-roe 15
# Output: [{"symbol": "XYZ", "score": 85, ...}, ...]

# All scripts follow the same pattern
python backend/analytics/risk/position_sizer.py --symbol AAPL --portfolio-value 100000
# Output: {"recommended_size": 2500, "kelly_fraction": 0.025, ...}
```

---

## Agent System

### Agent Types

**Data Agents** (call Python scripts, return structured data):
- `MarketRegimeAgent` — Current CMDS, FRS, market phase
- `ScreeningAgent` — Run stock screens based on criteria
- `RiskMonitorAgent` — Check systemic risks, portfolio exposure
- `TechnicalAgent` — Chart analysis, levels, momentum

**Research Agents** (use Claude API for synthesis):
- `FundamentalAnalystAgent` — Deep dive on individual stocks
- `SectorAnalystAgent` — Cross-industry pattern detection
- `DevilsAdvocateAgent` — Challenge your thesis, find risks
- `SentimentAnalystAgent` — Aggregate and interpret sentiment
- `EarningsAnalystAgent` — Parse transcripts, analyze guidance

**Action Agents** (recommend specific actions):
- `PositionSizerAgent` — Optimal allocation given risk
- `HedgeAdvisorAgent` — When/how to hedge
- `RebalancerAgent` — Portfolio optimization suggestions

### Agent Communication Protocol

```typescript
interface AgentRequest {
  agent: string;              // Which agent to call
  task: string;               // What to do
  context: {                  // Supporting data
    portfolio?: Portfolio;
    marketData?: MarketData;
    preferences?: UserPrefs;
  };
  options?: {
    depth?: 'quick' | 'deep'; // Analysis depth
    sources?: string[];       // Data sources to use
  };
}

interface AgentResponse {
  agent: string;
  status: 'success' | 'error';
  data: any;                  // Structured output
  reasoning?: string;         // Claude's analysis
  confidence?: number;        // 0-100
  sources: string[];          // Data sources used
  nextSteps?: string[];       // Suggested follow-ups
}
```

### Example Agent Workflow

```
User: "Should I buy more tech given current conditions?"

Orchestrator:
1. Call MarketRegimeAgent → Get CMDS (82 = EXTREME)
2. Call RiskMonitorAgent → Portfolio tech exposure (45%)
3. Call FundamentalAnalystAgent → Tech sector analysis
4. Call DevilsAdvocateAgent → What could go wrong?
5. Synthesize with Claude → Final recommendation

Response: Multi-paragraph analysis with data-backed reasoning
```

---

## User Interface

### Two Interaction Modes

**Chat Mode (Primary):**
- Natural language queries
- Agents respond with insights + visualizations
- Conversational drill-down
- Context-aware follow-ups

**Dashboard Mode:**
- Traditional panels showing real-time data
- Charts, gauges, heatmaps
- Click for drill-down details
- Three-screen layout (Market Overview, Opportunity Scanner, Portfolio Monitor)

### Example Chat Interaction

```
You: "I'm concerned about my tech exposure. What's the risk?"

[MarketRegimeAgent activates]
→ Calls cmds_calculator.py
→ Calls correlation_tracker.py  
→ Returns: CMDS 82 (EXTREME), Tech correlation 0.85

[RiskMonitorAgent activates]
→ Calls position_sizer.py
→ Returns: Tech position 45%, recommended max 25%

[Claude Synthesis]
"Given CMDS at 82 (EXTREME zone) and your tech exposure at 45%, 
you're overweight in the most vulnerable sector during high-risk 
conditions. Tech correlates 0.85 with S&P, offering little 
diversification benefit. Recommend reducing to 25% allocation.

Would you like me to:
1. Show specific positions to trim
2. Calculate hedge sizing
3. Find defensive alternatives"

You: "Show me defensive alternatives"

[ScreeningAgent activates]
→ Calls boring_business.py with defensive=true
→ Calls value_quality_momentum.py

[FundamentalAnalystAgent activates]
→ For each candidate, analyzes fundamentals
→ Claude synthesizes business quality

[Response with table of 10 stocks + detailed analysis]
```

---

## Data Layer

### Three Storage Types

**SQLite** (Relational):
- `cmds_history` — Daily scores over time
- `portfolio` — Current positions, P&L
- `trade_journal` — Every trade with thesis
- `watchlist` — Stocks being monitored
- `alerts` — Historical alert log

**JSON Files** (Cache):
- `data/cache/market_data/{symbol}_{date}.json`
- `data/cache/fred/{series}_{date}.json`
- `data/config/agent_preferences.json`
- `data/config/screening_criteria.json`

**Vector DB - ChromaDB/LanceDB** (Semantic Search):
- Earnings transcripts embeddings
- Historical research notes
- Pattern library (similar market conditions)
- Semantic search across past analyses

### Data Flow

1. Python scripts fetch from APIs (FRED, yfinance, pytrends)
2. Cache raw responses to JSON
3. Process and store structured results in SQLite
4. Generate embeddings for semantic search
5. Frontend queries SQLite for dashboard
6. Agents query vector DB for context-aware research

---

## Tech Stack

### Frontend Layer
- **Next.js 14+** — App router, server components
- **TypeScript** — Type safety throughout
- **TailwindCSS** — Styling
- **shadcn/ui** — Component primitives
- **Recharts/TradingView** — Charting
- **SWR** — Data fetching/caching

### Orchestration Layer
- **Node.js** — Agent coordination
- **Anthropic SDK** — Claude API calls
- **Zod** — Schema validation

### Analytics Layer
- **Python 3.11+** — Core analytics
- **FastAPI** — Minimal HTTP wrapper
- **pandas** — Data manipulation
- **scikit-learn** — ML models
- **yfinance** — Market data
- **pytrends** — Google Trends
- **fredapi** — Economic data

### Data Layer
- **SQLite** — Structured storage
- **ChromaDB/LanceDB** — Vector embeddings
- **JSON** — Config/cache

### Infrastructure
- **Electron** — Desktop wrapper
- **electron-builder** — Packaging
- **concurrently** — Dev process management

---

## Feature Requirements

### Phase 1: Core Monitoring Dashboard (Weeks 1-3)

#### 1.1 Market Risk Score System (PRIMARY FEATURE)

The centerpiece of RetailEdge is a **composite 0–100 Market Risk Score** that synthesizes multiple risk dimensions into a single, actionable number. This score then maps to a **probability of a ≥20% market correction** within 12–18 months.

**Core Formula:**
```
Probability(20%+ correction, 12–18m) ≈ 15% + (0.8 × RiskScore)
Capped between 5% and 95%
```

**Example Outputs:**
| Risk Score | Correction Probability | Interpretation |
|------------|----------------------|----------------|
| 25 | 35% | Moderate risk, normal positioning |
| 50 | 55% | Elevated risk, reduce leverage |
| 75 | 75% | High risk, defensive posture |
| 85+ | 83%+ | Extreme risk, maximum hedging |

---

**CATEGORY 1: Macro / Cycle (0–30 points)**

*"Where are we in the economic cycle?"*

Three sub-components, each 0–10 points, summed and capped at 30:

| Indicator | 0 Points | 5 Points | 10 Points | Data Source |
|-----------|----------|----------|-----------|-------------|
| **Unemployment Trend** | Flat or falling, ≤4% | Up 0.5–0.9pp from trough | Up ≥1.0pp from trough (Sahm rule trigger) | BLS via FRED |
| **Yield Curve Signal** | Never inverted recently | Briefly inverted, now modestly positive | Deep, long inversion followed by steepening | FRED T10Y2Y, T10Y3M |
| **GDP vs Stall Speed** | >2.5% trend growth | 1.5–2.5% growth | <1.5% or multiple weak/negative quarters | BEA via FRED |

**Current Assessment (Dec 2025):** ~25–28/30
- Unemployment: +10 (up ~1pp from 3.4% trough to 4.4%)
- Yield curve: +10 (historic 2+ year inversion, now steepening — classic pre-recession pattern)
- GDP: +7-8 (slowing toward stall speed, manufacturing in contraction)

**Implementation Notes:**
- Pull unemployment from FRED series `UNRATE`; calculate delta from rolling 12-month low
- Yield curve from `T10Y2Y` and `T10Y3M`; track inversion duration and depth
- GDP from `GDP` series; calculate trailing 4-quarter average growth rate

---

**CATEGORY 2: Valuation (0–25 points)**

*"How expensive are stocks relative to fundamentals?"*

Three sub-components, each 0–10 points, scaled to max 25:

| Indicator | 0 Points | 5 Points | 10 Points | Data Source |
|-----------|----------|----------|-----------|-------------|
| **Forward P/E vs Historical** | ≤ Historical median (~16x) | 1 SD above (~19-20x) | Dot-com/2021 levels (22x+) | S&P data, yfinance |
| **Buffett Indicator** | Normal range (<100%) | High but below prior peaks (100-140%) | At/above dot-com & 2007 highs (>140%) | FRED `NCBEILQ027S` / `GDP` |
| **Equity Yield vs T-Bills** | Earnings yield >> T-bill yield | Roughly equal | Equity yield < T-bill yield | Calculate: 1/PE vs 3-6mo T-bill |

**Current Assessment (Dec 2025):** ~25/25 (maximum)
- Forward P/E: +9-10 (S&P at 22-25x vs 15-18x historical average)
- Buffett Indicator: +10 (record highs, exceeding dot-com peak)
- Equity yield: +10 (5% T-bills vs ~4% earnings yield on stocks)

**Implementation Notes:**
- Forward P/E available from financial APIs or calculate from S&P earnings estimates
- Buffett Indicator: Total market cap (Wilshire 5000) / GDP
- T-bill yields from FRED `DTB3`, `DTB6`

---

**CATEGORY 3: Leverage & Financial Stability (0–25 points)**

*"Where are the hidden fragilities in the system?"*

Three sub-components, each 0–10 points, capped at 25:

| Indicator | 0 Points | 5 Points | 10 Points | Data Source |
|-----------|----------|----------|-----------|-------------|
| **Hedge Fund Leverage** | Low leverage, no basis-trade stress | Elevated but stable | Record leverage + concentration in Treasury/derivatives | Fed Financial Stability Report, FSOC |
| **Corporate Credit Health** | Tight spreads, strong coverage, low defaults | Mild deterioration | Widespread distress, defaults > historical medians | FRED HY spreads, default rate data |
| **CRE / Regional Bank Stress** | Low delinquency, no maturity concerns | Rising delinquency, manageable maturities | Record delinquency + large maturity wall + regulatory flags | FDIC data, commercial mortgage data |

**Current Assessment (Dec 2025):** ~25/25 (maximum)
- Hedge funds: +10 (record leverage per Fed, basis trade concentration)
- Corporate credit: +5-7 (spreads not blown out, but quality deteriorating, defaults rising)
- CRE: +9-10 (record office delinquency, $1T+ maturing 2024-26, regulators flagging risk)

**Implementation Notes:**
- HY spreads from FRED `BAMLH0A0HYM2` (ICE BofA HY spread)
- CRE delinquency rates from FDIC quarterly reports, commercial mortgage indices
- Hedge fund leverage requires manual input from Fed FSR (semi-annual)

---

**CATEGORY 4: Earnings & Margins (0–10 points)**

*"Are corporate profits sustainable?"*

| Indicator | 0 Points | 5 Points | 10 Points |
|-----------|----------|----------|-----------|
| **Breadth of Earnings Growth** | Broad-based across sectors | Mega-cap dominated | Earnings shrinking outside top 10 |
| **Margin Vulnerability** | Normal margins, low pressure | Some labor/interest pressure | Margins clearly compressing |

**Current Assessment (Dec 2025):** ~6/10
- Earnings still strong, but extremely concentrated in mega-caps
- Small caps under margin pressure from wages and interest costs
- Analyst forecasts assume near-record margins persist

**Implementation Notes:**
- Track earnings growth for S&P 500 vs equal-weighted index
- Monitor S&P 500 profit margins vs 10-year average
- Flag divergence between top 10 contributors and rest of index

---

**CATEGORY 5: Sentiment & Liquidity (–10 to +10 points)**

*"Is the crowd fearful or greedy? Is there dry powder?"*

This category can **add OR subtract** from total risk:

| Condition | Points | Interpretation |
|-----------|--------|----------------|
| Extreme fear + cash on sidelines | –10 to –5 | Contrarian bullish, buffer exists |
| Neutral sentiment | 0 | No adjustment |
| Euphoria + high leverage | +5 to +10 | Adds to risk score |

**Sub-indicators:**

| Indicator | Bearish/Defensive | Neutral | Bullish/Risky |
|-----------|------------------|---------|---------------|
| Consumer Confidence (Conf Board) | <70 | 70-100 | >100 |
| CEO Confidence Index | <40 | 40-60 | >60 |
| AAII Bull/Bear Spread | <-20% | -20% to +20% | >+20% bulls |
| Money Market Fund Assets | Record highs (dry powder) | Normal | Outflows to risk |
| VIX Level | >30 | 15-30 | <15 |

**Current Assessment (Dec 2025):** ~+4/10
- Consumer/CEO sentiment: Very weak (bullish for score — more fear)
- BUT: Record cash in money markets (~$6T+) provides buffer
- Net effect: Weak sentiment adds some risk, but massive cash stockpile means less euphoria

---

**MARKET RISK SCORE SUMMARY DASHBOARD**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MARKET RISK SCORE                                  │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                        TOTAL: 85/100                            │   │
│   │                  ████████████████████░░░░                       │   │
│   │                                                                 │   │
│   │         Correction Probability (12-18mo): ~83%                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│   Category Breakdown:                                                   │
│   ┌─────────────────────────┬─────────┬──────────────────────────────┐ │
│   │ Macro / Cycle           │  27/30  │ ██████████████████████████░  │ │
│   │ Valuation               │  25/25  │ ████████████████████████████ │ │
│   │ Leverage & Stability    │  25/25  │ ████████████████████████████ │ │
│   │ Earnings & Margins      │   6/10  │ ████████████░░░░░░░░░░░░░░░░ │ │
│   │ Sentiment & Liquidity   │  +4/10  │ ████████░░░░░░░░░░░░░░░░░░░░ │ │
│   └─────────────────────────┴─────────┴──────────────────────────────┘ │
│                                                                         │
│   [▼ Expand Details]  [📊 Historical Trend]  [⚙️ Adjust Weights]        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Action Triggers by Risk Score:**

| Score Range | Alert Level | Recommended Actions |
|-------------|-------------|---------------------|
| 0–30 | 🟢 GREEN | Full risk-on, deploy cash aggressively |
| 31–50 | 🟡 YELLOW | Normal positioning, modest hedges |
| 51–70 | 🟠 ORANGE | Reduce leverage, increase cash, add hedges |
| 71–85 | 🔴 RED | Defensive positioning, tight stops, significant hedges |
| 86–100 | ⚫ BLACK | Maximum defense, consider capital preservation mode |

---

#### 1.2 Your Volatility Predictor Integration (Tactical Layer)

While the Market Risk Score provides **strategic** (12-18 month) risk assessment, your Google Trends volatility predictor provides **tactical** (2-5 day) warning signals. These two systems complement each other:

| System | Timeframe | Purpose | Update Frequency |
|--------|-----------|---------|------------------|
| Market Risk Score | 12-18 months | Strategic allocation, hedge sizing | Weekly |
| Volatility Predictor | 2-5 days | Timing for entries/exits, stop adjustments | Daily |

**Volatility Predictor Components:**

1. **Fear Keyword Composite** (Primary Signal)
   - "stock crash," "recession," "bankruptcy," "layoffs"
   - Weighted by historical predictive accuracy
   - Normalized to 0-100 scale

2. **Search Volatility Detection** (Key Innovation)
   - Erratic search patterns more predictive than volume alone
   - Standard deviation of rolling searches signals imminent spike
   - 14-day volatility of search volume

3. **Cross-Asset Stress Overlay**
   - Treasury settlement fails (DTCC data)
   - Repo spread spikes (SOFR vs Fed Funds)
   - Crypto correlation to equities (flight-to-quality detector)

**Output Display:**
```
┌────────────────────────────────────────────────────────┐
│           VOLATILITY SPIKE PROBABILITY                 │
│                                                        │
│        ┌──────────────────────────────────┐            │
│        │          72%                      │            │
│        │   ████████████████░░░░░░░         │            │
│        │   2-5 Day Spike Probability       │            │
│        └──────────────────────────────────┘            │
│                                                        │
│   Signal Strength: ████████░░ 78%                      │
│   Confidence: ████████████░░ 85%                       │
│   Historical Accuracy: 67% (validated)                 │
│                                                        │
│   ⚠️ ALERT: Erratic search patterns detected           │
│   📊 Suggested hedge: Increase VIX position 2%         │
│                                                        │
│   [View Backtest] [Signal History] [Adjust Thresholds] │
└────────────────────────────────────────────────────────┘
```

**Integration with Market Risk Score:**

| Market Risk Score | Vol Predictor Signal | Combined Action |
|-------------------|---------------------|-----------------|
| <50 (Green/Yellow) | <50% | Normal operations |
| <50 (Green/Yellow) | >70% | Tighten stops temporarily |
| 50-70 (Orange) | <50% | Maintain defensive posture |
| 50-70 (Orange) | >70% | Add tactical hedges |
| >70 (Red/Black) | <50% | Stay defensive |
| >70 (Red/Black) | >70% | **Maximum alert** — consider reducing exposure |

---

#### 1.3 Combined Market Danger Score (CMDS) — The Unified Signal

The **Combined Market Danger Score** merges the Fundamental Risk Score (FRS) and Volatility Predictor (VP) into a single, actionable number that drives your allocation decisions. This is the **master signal** that tells you both *how dangerous the environment is* AND *whether danger is accelerating right now*.

**The Core Insight:**

| Component | What It Measures | Timeframe | Strength |
|-----------|-----------------|-----------|----------|
| **Fundamental Risk Score (FRS)** | Structural danger: valuations, macro cycle, leverage, credit stress | 12-18 months | Identifies big-picture fragility |
| **Volatility Predictor (VP)** | Sentiment acceleration: fear building, search patterns, warning spikes | 2-5 days | Excels at timing turning points |

Neither alone is sufficient:
- FRS without VP = You know it's dangerous, but not *when* to act
- VP without FRS = You catch short-term panic, but miss structural setups

**Together, they produce a far stronger signal than either alone.**

---

**CMDS Formula:**

```
CMDS = (0.65 × Fundamental Risk Score) + (0.35 × Volatility Predictor)
```

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Fundamental Risk Score | 65% | Reflects true underlying cycle; slow-moving but captures structural risk |
| Volatility Predictor | 35% | Adds timing precision; catches sentiment shifts before they manifest |

**Why This Weighting:**
- Fundamentals dominate because they determine the *magnitude* of potential corrections
- VP adds precision, helping you act at the *right time* within a risky environment
- A high FRS with low VP = "coiled spring" (danger building, catalyst not yet present)
- A low FRS with high VP = "noise" (short-term panic in stable environment)

---

**CMDS Calculation Example (Current State - December 2025):**

```
Fundamental Risk Score (FRS): 87/100
├── Macro / Cycle:        27/30
├── Valuation:            25/25
├── Leverage & Stability: 25/25
├── Earnings & Margins:    6/10
└── Sentiment Adjustment: +4/10

Volatility Predictor (VP): 72/100
├── Fear Keyword Composite: Elevated
├── Search Volatility: Erratic patterns detected
└── Cross-Asset Stress: Moderate

CMDS = (0.65 × 87) + (0.35 × 72)
     = 56.55 + 25.20
     = 81.75 → 82/100
```

---

**CMDS Dashboard Display:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              COMBINED MARKET DANGER SCORE (CMDS)                            │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │                          82/100                                   │     │
│   │     ████████████████████████████████████████░░░░░░░░░░            │     │
│   │                                                                   │     │
│   │              ⚠️  HIGH DANGER ZONE                                 │     │
│   │         Fundamentals + Timing Both Elevated                       │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│   Component Breakdown:                                                      │
│   ┌─────────────────────────────┬────────┬─────────┬───────────────────┐   │
│   │ Component                   │ Score  │ Weight  │ Contribution      │   │
│   ├─────────────────────────────┼────────┼─────────┼───────────────────┤   │
│   │ Fundamental Risk Score      │ 87/100 │  65%    │ 56.6 pts          │   │
│   │ Volatility Predictor        │ 72/100 │  35%    │ 25.2 pts          │   │
│   └─────────────────────────────┴────────┴─────────┴───────────────────┘   │
│                                                                             │
│   Signal Interpretation:                                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 🔴 BOTH ELEVATED: High confidence in near-term correction risk      │   │
│   │    → Structural fragility (FRS 87) WITH accelerating fear (VP 72)   │   │
│   │    → Recommended: Defensive allocation, active hedging              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│   [📊 Trend Chart]  [🔄 Refresh]  [⚙️ Adjust Weights]  [📋 Full Report]     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**CMDS Allocation Bands:**

The CMDS directly drives your portfolio allocation strategy:

| CMDS Range | Zone | Equity Allocation | Hedge Level | Cash Position | Posture |
|------------|------|-------------------|-------------|---------------|---------|
| 0–25 | 🟢 **SAFE** | 90-100% | None/Minimal | 0-10% | Full risk-on, deploy aggressively |
| 26–45 | 🟡 **CAUTIOUS** | 70-90% | Light (2-5%) | 10-20% | Normal positioning, modest protection |
| 46–65 | 🟠 **ELEVATED** | 50-70% | Moderate (5-10%) | 20-35% | Reduce leverage, increase cash |
| 66–80 | 🔴 **HIGH** | 30-50% | Significant (10-15%) | 35-50% | Defensive positioning, tight stops |
| 81–100 | ⚫ **EXTREME** | 10-30% | Maximum (15-25%) | 50-75% | Capital preservation mode |

**Current Position (CMDS = 82):** ⚫ EXTREME — Consider 10-30% equity, 15-25% hedges, 50-75% cash/bonds

---

**Divergence Interpretation:**

When FRS and VP diverge, the model provides nuanced guidance:

| Scenario | FRS | VP | CMDS | Interpretation | Action |
|----------|-----|-----|------|----------------|--------|
| **Coiled Spring** | High (>70) | Low (<40) | Moderate | Structural risk present but no catalyst yet | Stay defensive, watch VP for timing |
| **False Alarm** | Low (<40) | High (>70) | Moderate | Short-term panic in stable environment | Potential buying opportunity if fundamentals sound |
| **Aligned Danger** | High (>70) | High (>70) | High | Both structure AND timing signal danger | Maximum defense, highest conviction |
| **All Clear** | Low (<40) | Low (<40) | Low | Healthy environment, no imminent risk | Full risk-on positioning |

**Key Principle:** 
- **Fundamentals set the trend** — they tell you the *magnitude* of risk
- **VP sets the timing** — it tells you *when* to act

When both rise together, confidence in a correction increases dramatically.

---

**CMDS Alert Triggers:**

| Trigger | Condition | Alert Type | Action |
|---------|-----------|------------|--------|
| Zone Change | CMDS crosses allocation band threshold | Push + Email | Review allocation immediately |
| Rapid Rise | CMDS increases >15 points in 7 days | Push | Emergency review |
| Divergence Alert | FRS and VP differ by >40 points | Email | Investigate which signal is leading |
| Extreme Entry | CMDS exceeds 80 | Push + SMS | Crisis protocol activation |
| Recovery Signal | CMDS drops below 50 after being >70 | Email | Consider re-risking |

---

#### 1.4 Alert System

**Tier 1 - Immediate Action (Push Notification + SMS)**
- **CMDS exceeds 80** (Extreme zone entry)
- **CMDS increases >15 points in 7 days** (Rapid deterioration)
- Volatility predictor >80% confidence spike
- Any position down >7% (stop-loss review)
- Systemic risk metric >2 standard deviation move

**Tier 2 - Review Within 24 Hours (Email)**
- **CMDS crosses allocation band threshold** (Zone change)
- **FRS and VP diverge by >40 points** (Investigate leading signal)
- Market regime category change
- Earnings surprise >10% in watchlist stock
- Insider activity >$1M in held position
- Sentiment extreme (<10th or >90th percentile)

**Tier 3 - Weekly Review (Dashboard Badge)**
- **CMDS trend analysis** (direction and velocity)
- New stocks meeting screening criteria
- Sector rotation shifts
- Valuation metrics crossing thresholds
- Performance vs benchmark summary

**Implementation**
- Email alerts via SMTP (or Twilio for SMS)
- Push notifications via browser service worker
- Alert history log with action taken/outcome tracking

---

### Phase 2: AI Integration & Stock Selection (Weeks 4-8)

#### 2.1 Quantitative Screens

**"Gems in the Rough" Scanner**
Your thesis: find overlooked stocks in unsexy industries

Screening criteria:
- Value: P/E <15, P/B <2, PEG <1
- Quality: ROE >15%, Debt/EBITDA <3, positive FCF
- Momentum: 6-month positive price momentum, earnings surprise trend
- Neglect filter: <5 analyst coverage, <20% institutional ownership
- Industry filter: Industrials, materials, specialty chemicals (exclude tech)
- Insider signal: Management buying >$500K in last 3 months

**Turnaround Template**
- Stocks down >40% from highs
- Recent management change or strategic pivot
- Improving margins (sequential quarterly trend)
- Stabilizing revenue (sequential growth)
- Debt manageable (covenant cushion >20%)

**Output**
- Weekly ranked list with conviction scores
- Entry/exit price suggestions based on technical levels
- Correlation to existing portfolio positions

#### 2.2 LLM-Powered Analysis ("Connection Machine")

**Integration: Anthropic Claude API**

**Automated Research Tasks**

1. **Cross-Industry Pattern Detection**
   - Prompt template: "Analyze how [trend] affects these 10 sectors. Which companies benefit from second-order effects?"
   - Scan earnings transcripts for emerging themes
   - Identify non-obvious beneficiaries of macro shifts

2. **Sentiment Synthesis**
   - Aggregate analyst reports, news, social media
   - Flag sentiment/fundamentals divergences
   - Track narrative shifts (e.g., "AI infrastructure" → "AI monetization")

3. **Devil's Advocate Analysis**
   - For each position: "What would make this thesis wrong?"
   - Forced bear case generation
   - Risk factor scoring and ranking

4. **Earnings Call Analysis**
   - Automatic summarization of key points
   - Management tone analysis (hedging language, confidence markers)
   - Guidance comparison and peer commentary synthesis

#### 2.3 Sentiment Aggregator

**Data Sources**
- AAII Bull/Bear spread
- Put/Call ratios (equity, index, individual)
- VIX term structure (contango/backwardation)
- Conference Board Consumer Confidence
- CEO Confidence Index
- NFIB Small Business Optimism
- University of Michigan Sentiment

**Composite Output**
- Historical percentile ranking (0-100)
- Contrarian signals at extremes (<20th or >80th percentile)
- Overlay with technical support/resistance levels

---

### Phase 3: Portfolio Management & Risk Tools (Weeks 9-12)

#### 3.1 Portfolio Monitor

**Current Positions View**
- Real-time P&L (unrealized and realized)
- Cost basis tracking
- Dividend income tracking
- Tax lot management view

**Risk Metrics**
- Portfolio beta to S&P 500
- Sector concentration (warning at >25% any sector)
- Current drawdown vs maximum acceptable
- Correlation matrix between holdings
- Hedge effectiveness (P&L contribution on down days)

**Cash Deployment Pacing**
- If market down X%, deploy Y% of reserves
- Visual guide showing deployment levels
- Historical entry point optimization

#### 3.2 Position Sizing Calculator

**Kelly Criterion Implementation (with safety factor)**

Inputs:
- Win probability (from model predictions)
- Payoff ratio (expected gain/loss ratio)
- Correlation to existing positions
- Portfolio risk tolerance setting

Outputs:
- Optimal position size (% of portfolio)
- Adjusted size for correlation clustering
- Max position cap enforcement

#### 3.3 Trade Journal

**Automatic Logging**
- Entry/exit date, price, size
- Thesis at entry (free text + tags)
- Signals that triggered the trade
- Outcome and P&L

**Performance Analytics**
- Win rate by signal type
- Average holding period by strategy
- Best/worst performing setups
- Regime-adjusted performance

---

### Phase 4: Systemic Risk Monitoring (Weeks 13-16)

#### 4.1 Treasury Market Stress Index

**Metrics**
- Bid-ask spreads on 10-year Treasury
- Market depth indicators
- Settlement fails (DTCC data, warning >$50B)
- Repo spreads (SOFR-TGCR, SOFR vs Fed Funds)
- Auction quality (bid-to-cover, dealer takedown %)

**Alert Levels**
- Green: Normal conditions
- Yellow: Reduce leverage
- Red: Maximum defensive positioning

#### 4.2 Credit Stress Dashboard

**Monitoring**
- Corporate spreads (IG vs HY, BBB crossover)
- Leveraged loan default rate
- CRE delinquency rates by property type
- Regional bank health (CDS spreads, deposit flows)
- Distressed debt ratio (% trading <80 cents)

#### 4.3 Contagion Early Warning

**Cross-Asset Correlation Tracking**
- Stock-bond correlation shifts
- Bitcoin-Nasdaq correlation
- Dollar index volatility
- Gold/stocks ratio, copper/gold ratio
- Europe bank CDS, China property bonds

**Pattern Recognition**
- Alert when correlations converge toward 1.0
- Historical comparison to prior stress episodes

---

## Development Workflow

### Iterative Module Building

**Week 1-2: Core Infrastructure**
- [ ] Set up Electron + Next.js shell
- [ ] Create Python FastAPI wrapper
- [ ] Build core analytics modules:
  - [ ] `cmds_calculator.py` — Combined Market Danger Score
  - [ ] `frs_calculator.py` — Fundamental Risk Score
  - [ ] `volatility_predictor.py` — Your existing Google Trends model
- [ ] Test each module independently via CLI

**Week 3-4: First Agents**
- [ ] Implement `MarketRegimeAgent` (calls CMDS, FRS, VP scripts)
- [ ] Implement `ScreeningAgent` (calls screening scripts)
- [ ] Build basic chat interface
- [ ] Connect agents to frontend

**Week 5-6: Research Agents**
- [ ] Add `FundamentalAnalystAgent`
- [ ] Add `DevilsAdvocateAgent`
- [ ] Implement vector DB for context
- [ ] Multi-step agent workflows

**Week 7-8: Risk & Portfolio**
- [ ] Position sizing logic (`position_sizer.py`)
- [ ] Portfolio tracking (SQLite schema)
- [ ] Alert system integration
- [ ] Historical backtesting framework

**Ongoing: Expand Analytics**
- Each week add 2-3 new Python modules
- Modules are independent, delivering incremental value
- Agent orchestrator automatically discovers new capabilities

### Testing Pattern

```bash
# Test Python module in isolation
python -m pytest tests/test_cmds_calculator.py

# Test via HTTP API
curl http://localhost:8000/api/cmds

# Test agent orchestration
npm run test:agents

# Integration test in Electron
npm run dev
```

---

## Success Metrics

### Quantitative Goals

| Metric | Target | Measurement |
|--------|--------|-------------|
| **CMDS zone accuracy** | High CMDS (>70) precedes corrections 75%+ | Historical backtest |
| **FRS accuracy** | Elevated FRS (>70) precedes corrections 80%+ | Historical backtest validation |
| **VP timing accuracy** | 60-70% spike prediction | Rolling 90-day backtest |
| **CMDS false positive rate** | <25% | High scores without subsequent correction |
| Alert relevance | >80% useful | User feedback logging |
| Time savings | 50% reduction in research time | Self-reported tracking |
| Portfolio performance | Beat S&P 500 risk-adjusted | Sharpe ratio comparison |
| System uptime | >99% during market hours | Monitoring logs |

### Qualitative Goals

- Feel informed rather than anxious about market moves
- Make decisions with clear, documented reasoning
- Identify opportunities before mainstream attention
- Understand portfolio risk in real-time
- Maintain discipline through systematic processes

---

## Risk & Limitations

### Technical Risks

| Risk | Mitigation |
|------|------------|
| API rate limits | Caching, request batching, multiple providers |
| Data quality issues | Validation layers, cross-source verification |
| Model degradation | Continuous backtesting, accuracy monitoring |
| System downtime | Local fallback, critical alert redundancy |

### Methodological Limitations

1. **Cannot Predict Black Swans**: Totally unexpected events (pandemic, geopolitical shock) won't appear in historical patterns
2. **Directional Uncertainty**: System predicts volatility, not whether market goes up or down
3. **Self-Fulfilling Risk**: If methodology becomes mainstream, edge diminishes
4. **LLM Limitations**: Cannot access real-time data, may hallucinate facts—always verify

### Important Disclaimers

- This is a decision-support tool, not financial advice
- Past performance doesn't guarantee future results
- All models are wrong, some are useful
- Maintain position sizing discipline regardless of conviction

---

## Budget Considerations

### Free/Low-Cost Options

| Service | Cost | Notes |
|---------|------|-------|
| Yahoo Finance (yfinance) | Free | Reliable for daily data |
| Google Trends (pytrends) | Free | Your existing data source |
| FRED API | Free | Economic indicators |
| Alpha Vantage | Free tier: 5 calls/min | Real-time quotes |
| Claude API | ~$15/month estimated | Batch analysis, not real-time |
| Hosting (local) | Free | Development phase |

### Optional Upgrades

| Service | Cost | Benefit |
|---------|------|---------|
| Polygon.io | $29/month | Better real-time data |
| Twilio SMS | ~$5/month | Mobile alerts |
| Railway/Heroku hosting | $5-20/month | Cloud deployment |
| News API | $0-100/month | Broader sentiment sources |

**Estimated Total: $0-50/month for full functionality**

---

## Getting Started

### Project Setup

1. **Create project structure**
   ```bash
   mkdir tradeedge && cd tradeedge
   
   # Python analytics backend
   mkdir -p backend/analytics/{core,screening,risk,technical,data_fetchers}
   mkdir -p backend/tests
   mkdir -p data/{cache,config}
   
   # Frontend (Next.js + Electron)
   npx create-next-app@latest frontend --typescript --tailwind
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install fastapi uvicorn pandas yfinance pytrends fredapi scikit-learn anthropic
   pip install pytest  # for testing
   ```

3. **Build first analytics module**
   ```bash
   # Start with your volatility predictor
   cp /path/to/existing/volatility_predictor.py backend/analytics/core/
   
   # Test it works standalone
   python backend/analytics/core/volatility_predictor.py
   ```

4. **Create FastAPI wrapper**
   ```bash
   # backend/main.py
   uvicorn main:app --reload
   ```

5. **Build iteratively**
   - Add one Python module at a time
   - Test each via CLI before integrating
   - Connect to frontend via HTTP API

---

## Appendix: Key Data Sources Reference

| Source | Data Type | API/Access | Update Frequency |
|--------|-----------|------------|------------------|
| Yahoo Finance | Price, fundamentals | yfinance library | Real-time/daily |
| Google Trends | Search behavior | pytrends library | Weekly |
| FRED | Economic indicators | fredapi library | Varies by series |
| FINRA | Short interest | Manual/API | Bi-monthly |
| SEC EDGAR | 13F filings, insider trades | API | Quarterly/as filed |
| DTCC | Settlement data | Manual | Daily |
| AAII | Sentiment surveys | Manual | Weekly |

---

## Appendix A: Market Risk Score Implementation Guide

### Data Sources by Category

**Category 1: Macro / Cycle**
```python
# FRED API calls for macro indicators
MACRO_SERIES = {
    'unemployment': 'UNRATE',           # Monthly unemployment rate
    'yield_10y2y': 'T10Y2Y',            # 10Y-2Y spread
    'yield_10y3m': 'T10Y3M',            # 10Y-3M spread  
    'gdp_growth': 'A191RL1Q225SBEA',    # Real GDP growth rate
    'pmi_mfg': 'MANEMP',                # Manufacturing employment proxy
}
```

**Category 2: Valuation**
```python
# Valuation data sources
VALUATION_SOURCES = {
    'sp500_pe': 'yfinance SPY or calculate from earnings',
    'buffett_indicator': 'NCBEILQ027S / GDP',  # Market cap / GDP
    'tbill_3mo': 'DTB3',                       # 3-month T-bill
    'tbill_6mo': 'DTB6',                       # 6-month T-bill
}
```

**Category 3: Leverage & Stability**
```python
# Credit and leverage indicators
LEVERAGE_SOURCES = {
    'hy_spread': 'BAMLH0A0HYM2',        # ICE BofA HY spread
    'ig_spread': 'BAMLC0A4CBBB',        # BBB corporate spread
    'ted_spread': 'TEDRATE',             # TED spread (credit stress)
    # Note: Hedge fund leverage requires manual input from Fed FSR
}
```

**Category 4: Earnings**
```python
# Earnings breadth tracking
EARNINGS_METRICS = {
    'sp500_earnings': 'S&P reported/estimated EPS',
    'equal_weight_vs_cap': 'RSP vs SPY performance',
    'profit_margins': 'S&P 500 net margins',
}
```

**Category 5: Sentiment**
```python
# Sentiment aggregation
SENTIMENT_SOURCES = {
    'consumer_conf': 'Conference Board (manual)',
    'michigan_sent': 'University of Michigan (UMCSENT)',
    'aaii_survey': 'AAII.com weekly (manual)',
    'vix': '^VIX via yfinance',
    'mmf_assets': 'Money market fund flows',
}
```

### Scoring Algorithm Pseudocode

```python
def calculate_market_risk_score():
    """
    Calculate composite market risk score (0-100)
    Returns: risk_score, correction_probability, category_breakdown
    """
    
    # Category 1: Macro/Cycle (0-30)
    unemployment_score = score_unemployment_trend()      # 0-10
    yield_curve_score = score_yield_curve()              # 0-10
    gdp_score = score_gdp_vs_stall()                     # 0-10
    macro_score = min(30, unemployment_score + yield_curve_score + gdp_score)
    
    # Category 2: Valuation (0-25)
    pe_score = score_forward_pe()                        # 0-10
    buffett_score = score_buffett_indicator()            # 0-10
    equity_yield_score = score_equity_vs_tbill()         # 0-10
    valuation_raw = pe_score + buffett_score + equity_yield_score
    valuation_score = min(25, valuation_raw * 25 / 30)   # Scale to 25
    
    # Category 3: Leverage & Stability (0-25)
    hedge_fund_score = score_hedge_fund_leverage()       # 0-10 (manual input)
    corp_credit_score = score_corporate_credit()         # 0-10
    cre_score = score_cre_stress()                       # 0-10
    leverage_raw = hedge_fund_score + corp_credit_score + cre_score
    leverage_score = min(25, leverage_raw * 25 / 30)     # Scale to 25
    
    # Category 4: Earnings (0-10)
    earnings_score = score_earnings_breadth()            # 0-10
    
    # Category 5: Sentiment (-10 to +10)
    sentiment_score = score_sentiment_liquidity()        # -10 to +10
    
    # Total Risk Score
    risk_score = macro_score + valuation_score + leverage_score + earnings_score + sentiment_score
    risk_score = max(0, min(100, risk_score))            # Clamp to 0-100
    
    # Calculate correction probability
    correction_prob = 15 + (0.8 * risk_score)
    correction_prob = max(5, min(95, correction_prob))   # Clamp to 5-95%
    
    return {
        'risk_score': risk_score,
        'correction_probability': correction_prob,
        'breakdown': {
            'macro': macro_score,
            'valuation': valuation_score,
            'leverage': leverage_score,
            'earnings': earnings_score,
            'sentiment': sentiment_score,
        }
    }
```

### Current Baseline Assessment (December 2025)

Based on your research documents:

| Category | Current Score | Key Drivers |
|----------|---------------|-------------|
| Macro / Cycle | 27/30 | Unemployment +1pp from trough, yield curve recently uninverted after 2-year inversion, GDP slowing |
| Valuation | 25/25 | Forward P/E 22-25x (vs 16x historical), Buffett Indicator at record, equities yield < T-bills |
| Leverage | 25/25 | Record hedge fund leverage, CRE delinquency spiking, corporate refinancing cliff |
| Earnings | 6/10 | Concentrated in mega-caps, small-cap margin pressure |
| Sentiment | +4/10 | Weak consumer/CEO confidence, BUT record money market cash provides buffer |
| **TOTAL** | **~87/100** | **~85% correction probability (12-18mo)** |

### Model Validation Approach

1. **Backtest Against Historical Corrections**
   - 2000 Dot-com crash
   - 2008 Financial crisis
   - 2020 COVID crash
   - 2022 Tech correction

2. **Key Questions to Validate:**
   - What was the risk score 6-12 months before each correction?
   - Did the model produce false positives (high scores without corrections)?
   - Which categories had the most predictive power?

3. **Calibration Parameters to Tune:**
   - The 0.8 multiplier in the probability formula
   - Category weightings
   - Individual indicator thresholds

---

## Appendix B: Combined Market Danger Score (CMDS) Implementation

### CMDS Calculation Algorithm

```python
def calculate_cmds(frs: float, vp: float, 
                   frs_weight: float = 0.65, 
                   vp_weight: float = 0.35) -> dict:
    """
    Calculate Combined Market Danger Score
    
    Args:
        frs: Fundamental Risk Score (0-100)
        vp: Volatility Predictor score (0-100)
        frs_weight: Weight for fundamentals (default 65%)
        vp_weight: Weight for volatility predictor (default 35%)
    
    Returns:
        dict with CMDS score, allocation guidance, and interpretation
    """
    
    # Calculate combined score
    cmds = (frs_weight * frs) + (vp_weight * vp)
    cmds = max(0, min(100, cmds))  # Clamp to 0-100
    
    # Determine allocation zone
    if cmds <= 25:
        zone = 'SAFE'
        equity_range = (90, 100)
        hedge_range = (0, 2)
        cash_range = (0, 10)
    elif cmds <= 45:
        zone = 'CAUTIOUS'
        equity_range = (70, 90)
        hedge_range = (2, 5)
        cash_range = (10, 20)
    elif cmds <= 65:
        zone = 'ELEVATED'
        equity_range = (50, 70)
        hedge_range = (5, 10)
        cash_range = (20, 35)
    elif cmds <= 80:
        zone = 'HIGH'
        equity_range = (30, 50)
        hedge_range = (10, 15)
        cash_range = (35, 50)
    else:
        zone = 'EXTREME'
        equity_range = (10, 30)
        hedge_range = (15, 25)
        cash_range = (50, 75)
    
    # Analyze divergence
    divergence = abs(frs - vp)
    if divergence > 40:
        if frs > vp:
            divergence_interpretation = "COILED_SPRING: Structural risk high, catalyst not yet present"
        else:
            divergence_interpretation = "FALSE_ALARM: Short-term panic in stable environment"
    elif frs > 70 and vp > 70:
        divergence_interpretation = "ALIGNED_DANGER: Both signals confirm high risk"
    elif frs < 40 and vp < 40:
        divergence_interpretation = "ALL_CLEAR: Healthy environment"
    else:
        divergence_interpretation = "MIXED: Monitor for clarity"
    
    return {
        'cmds': round(cmds, 1),
        'zone': zone,
        'allocation': {
            'equity_pct': equity_range,
            'hedge_pct': hedge_range,
            'cash_pct': cash_range,
        },
        'components': {
            'frs': frs,
            'frs_contribution': round(frs_weight * frs, 1),
            'vp': vp,
            'vp_contribution': round(vp_weight * vp, 1),
        },
        'divergence': divergence,
        'interpretation': divergence_interpretation,
    }


def check_cmds_alerts(current_cmds: float, 
                      previous_cmds: float, 
                      cmds_7d_ago: float,
                      frs: float, 
                      vp: float) -> list:
    """
    Check for CMDS-based alert conditions
    
    Returns:
        List of triggered alerts with severity
    """
    alerts = []
    
    # Extreme zone entry
    if current_cmds > 80 and previous_cmds <= 80:
        alerts.append({
            'type': 'EXTREME_ENTRY',
            'severity': 'CRITICAL',
            'message': f'CMDS entered EXTREME zone: {current_cmds:.1f}',
            'action': 'Crisis protocol - review all positions immediately'
        })
    
    # Rapid rise (>15 points in 7 days)
    if cmds_7d_ago and (current_cmds - cmds_7d_ago) > 15:
        alerts.append({
            'type': 'RAPID_RISE',
            'severity': 'HIGH',
            'message': f'CMDS rose {current_cmds - cmds_7d_ago:.1f} pts in 7 days',
            'action': 'Emergency allocation review'
        })
    
    # Zone change
    prev_zone = get_zone(previous_cmds)
    curr_zone = get_zone(current_cmds)
    if prev_zone != curr_zone:
        alerts.append({
            'type': 'ZONE_CHANGE',
            'severity': 'MEDIUM',
            'message': f'CMDS zone changed: {prev_zone} → {curr_zone}',
            'action': 'Adjust allocation to new band'
        })
    
    # FRS/VP divergence
    if abs(frs - vp) > 40:
        alerts.append({
            'type': 'DIVERGENCE',
            'severity': 'LOW',
            'message': f'FRS ({frs:.0f}) and VP ({vp:.0f}) diverged by {abs(frs-vp):.0f} pts',
            'action': 'Investigate which signal is leading'
        })
    
    # Recovery signal
    if current_cmds < 50 and previous_cmds >= 70:
        alerts.append({
            'type': 'RECOVERY',
            'severity': 'INFO',
            'message': f'CMDS dropped to {current_cmds:.1f} from elevated levels',
            'action': 'Consider gradual re-risking'
        })
    
    return alerts


def get_zone(cmds: float) -> str:
    """Helper to get zone name from CMDS value"""
    if cmds <= 25: return 'SAFE'
    elif cmds <= 45: return 'CAUTIOUS'
    elif cmds <= 65: return 'ELEVATED'
    elif cmds <= 80: return 'HIGH'
    else: return 'EXTREME'
```

### CMDS Historical Backtest Framework

```python
def backtest_cmds(historical_data: pd.DataFrame, 
                  correction_threshold: float = -0.20,
                  lookahead_months: int = 18) -> dict:
    """
    Backtest CMDS against historical corrections
    
    Args:
        historical_data: DataFrame with dates, FRS, VP, and S&P 500 returns
        correction_threshold: What constitutes a "correction" (default -20%)
        lookahead_months: Prediction window (default 18 months)
    
    Returns:
        Backtest results including hit rate, false positives, timing
    """
    results = {
        'high_cmds_corrections': 0,    # CMDS > 70 followed by correction
        'high_cmds_no_correction': 0,  # False positives
        'low_cmds_corrections': 0,     # Missed corrections
        'low_cmds_no_correction': 0,   # True negatives
        'avg_lead_time_days': [],      # Days between signal and correction
    }
    
    # Implementation would iterate through historical data
    # comparing CMDS readings to subsequent market performance
    
    return results
```

### Current CMDS Assessment (December 2025)

| Component | Score | Contribution |
|-----------|-------|--------------|
| Fundamental Risk Score | 87/100 | 56.6 pts (65% weight) |
| Volatility Predictor | 72/100 | 25.2 pts (35% weight) |
| **Combined CMDS** | **82/100** | **EXTREME Zone** |

**Interpretation:** Both structural risk (FRS 87) and timing signals (VP 72) are elevated. This "aligned danger" pattern historically precedes significant corrections with high confidence.

**Recommended Allocation:**
- Equities: 10-30%
- Hedges: 15-25%
- Cash/Bonds: 50-75%

---

## Appendix C: Weight Calibration Guidance

### Why 65/35 for FRS/VP?

The default 65/35 weighting was chosen based on these principles:

1. **Fundamentals are Persistent**: Structural risks (valuations, leverage, macro) tend to persist for months, giving you time to position. They deserve majority weight because they determine correction *magnitude*.

2. **VP Adds Alpha Through Timing**: The volatility predictor catches sentiment shifts 2-5 days ahead, allowing you to optimize *when* to act within a risky environment.

3. **Avoid Overreacting to Noise**: A 35% VP weight means short-term fear spikes won't whipsaw your allocation if fundamentals are sound.

### Customization Options

| Investor Profile | FRS Weight | VP Weight | Rationale |
|------------------|------------|-----------|-----------|
| Long-term holder | 75% | 25% | Less concerned with timing |
| Active trader | 50% | 50% | Timing matters equally |
| Risk-averse | 60% | 40% | More responsive to fear signals |
| Default | 65% | 35% | Balanced approach |

### Weight Sensitivity Analysis

How CMDS changes with different weightings (FRS=87, VP=72):

| FRS Weight | VP Weight | CMDS | Zone |
|------------|-----------|------|------|
| 50% | 50% | 79.5 | HIGH |
| 60% | 40% | 81.0 | EXTREME |
| **65%** | **35%** | **81.8** | **EXTREME** |
| 70% | 30% | 82.5 | EXTREME |
| 75% | 25% | 83.3 | EXTREME |

In the current high-risk environment, the zone doesn't change much with weighting—both signals are elevated.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 2025 | Initial PRD |
| 1.1 | December 2025 | Added Market Risk Score (FRS) model as core monitoring feature |
| 1.2 | December 2025 | Added Combined Market Danger Score (CMDS) integrating FRS + Volatility Predictor with 65/35 weighting, allocation bands, divergence analysis |
| 2.0 | December 2025 | **Major architecture update**: Renamed to TradeEdge, adopted modular Python "brains" architecture, agent-based orchestration, chat-first interface, Electron/Next.js frontend. Removed template dependencies—each script is now independent. |

---

*This document serves as the foundational specification for TradeEdge. It should be updated as the project evolves and requirements become clearer through development and usage.*

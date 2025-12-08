## TradeEdge High-Level Architecture

### **System Overview**

```
┌─────────────────────────────────────────────────────┐
│              ELECTRON SHELL                         │
│  ┌───────────────────────────────────────────────┐  │
│  │         NEXT.JS FRONTEND                      │  │
│  │  - Dashboard UI (3-screen layout)            │  │
│  │  - Chat Interface (primary interaction)      │  │
│  │  - Data Visualizations                       │  │
│  └───────────────────────────────────────────────┘  │
│                        ↕                            │
│  ┌───────────────────────────────────────────────┐  │
│  │      AGENT ORCHESTRATOR (Node.js)            │  │
│  │  - Routes tasks to specialized agents        │  │
│  │  - Manages conversation context              │  │
│  │  - Coordinates multi-agent workflows         │  │
│  └───────────────────────────────────────────────┘  │
│                        ↕                            │
│  ┌───────────────────────────────────────────────┐  │
│  │      PYTHON ANALYTICS ENGINE                 │  │
│  │  - Standalone modular scripts                │  │
│  │  - Each independently testable               │  │
│  │  - Simple HTTP API wrapper                   │  │
│  └───────────────────────────────────────────────┘  │
│                        ↕                            │
│  ┌───────────────────────────────────────────────┐  │
│  │      LOCAL DATA LAYER                        │  │
│  │  - SQLite (structured data)                  │  │
│  │  - JSON files (configs, cache)               │  │
│  │  - Vector DB (embeddings, memory)            │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Core Components

### **1. Python Analytics Engine (The Brain)**

**Design Principle:** Each script is a pure function - takes input, returns output. No shared state. No dependencies on each other.

**Module Structure:**

```
backend/analytics/
├── core/
│   ├── cmds_calculator.py          # CMDS score
│   ├── frs_calculator.py           # Fundamental risk
│   ├── volatility_predictor.py     # Google Trends model
│   ├── market_internals.py         # Breadth, concentration
│   └── valuation_metrics.py        # P/E, Buffett indicator
├── screening/
│   ├── value_quality_momentum.py   # VQM scanner
│   ├── boring_business.py          # Unsexy industry filter
│   ├── turnaround_detector.py      # Recovery opportunities
│   └── insider_tracker.py          # Management buying
├── risk/
│   ├── treasury_stress.py          # Bond market health
│   ├── credit_monitor.py           # HY spreads, CRE
│   ├── position_sizer.py           # Kelly criterion
│   └── correlation_tracker.py      # Portfolio correlations
├── technical/
│   ├── trend_analyzer.py           # Multi-timeframe
│   ├── support_resistance.py       # Key levels
│   └── volume_profile.py           # Unusual activity
└── data_fetchers/
    ├── fred_client.py              # Economic data
    ├── yfinance_client.py          # Market data
    └── sentiment_aggregator.py     # News, social
```

**Key Design Rules:**

- Each script has a `main()` function callable from CLI
- Outputs JSON to stdout for testing
- HTTP API is just a thin wrapper calling these scripts
- Scripts cache their own data locally
- No script depends on another script running first

**Example Interface:**

```bash
# Test individual script
python backend/analytics/core/cmds_calculator.py
# Output: {"cmds": 82, "frs": 87, "vp": 72, "zone": "EXTREME"}

# All scripts follow same pattern
python backend/analytics/screening/boring_business.py --min-roe 15
# Output: [{"symbol": "XYZ", "score": 85, ...}, ...]
```

### **2. Agent Orchestrator (The Conductor)**

**Purpose:** Routes user queries to the right combination of agents, coordinates multi-step research.

**Agent Types:**

**Data Agents** (call Python scripts, return structured data):

- `MarketRegimeAgent` - Current CMDS, FRS, market phase
- `ScreeningAgent` - Run stock screens based on criteria
- `RiskMonitorAgent` - Check systemic risks, portfolio exposure
- `TechnicalAgent` - Chart analysis, levels, momentum

**Research Agents** (use Claude API for synthesis):

- `FundamentalAnalystAgent` - Deep dive on individual stocks
- `SectorAnalystAgent` - Cross-industry pattern detection
- `DevilsAdvocateAgent` - Challenge your thesis, find risks
- `SentimentAnalystAgent` - Aggregate and interpret sentiment
- `EarningsAnalystAgent` - Parse transcripts, guidance

**Action Agents** (recommend specific actions):

- `PositionSizerAgent` - Optimal allocation given risk
- `HedgeAdvisorAgent` - When/how to hedge
- `RebalancerAgent` - Portfolio optimization suggestions

**Orchestrator Flow:**

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

### **3. Next.js Frontend (The Interface)**

**Two Interaction Modes:**

**Dashboard Mode:**

- Traditional panels showing real-time data
- Charts, gauges, heatmaps
- Click for drill-down details

**Chat Mode** (Primary):

- Natural language queries
- Agents respond with insights + visualizations
- Conversational drill-down
- Context-aware follow-ups

**Component Structure:**

```
frontend/
├── app/
│   ├── dashboard/          # Traditional view
│   └── chat/              # Agent interface
├── components/
│   ├── agents/
│   │   ├── AgentResponse.tsx    # Format agent output
│   │   ├── DataTable.tsx        # Screening results
│   │   └── ChartEmbed.tsx       # Inline visualizations
│   ├── charts/
│   │   ├── CMDSGauge.tsx
│   │   ├── SectorHeatmap.tsx
│   │   └── PortfolioRisk.tsx
│   └── chat/
│       ├── MessageList.tsx
│       ├── AgentSelector.tsx    # Choose which agents to activate
│       └── ContextPanel.tsx     # Show what data agents used
└── lib/
    ├── orchestrator.ts      # Agent coordination logic
    ├── python-bridge.ts     # Call Python API
    └── agents/              # Agent definitions
        ├── base-agent.ts
        └── specialized-agents.ts
```

### **4. Data Layer (The Memory)**

**Three Storage Types:**

**SQLite** (Relational):

- `cmds_history` - Daily scores over time
- `portfolio` - Current positions, P&L
- `trade_journal` - Every trade with thesis
- `watchlist` - Stocks being monitored
- `alerts` - Historical alert log

**JSON Files** (Cache):

- `data/cache/market_data/{symbol}_{date}.json`
- `data/cache/fred/{series}_{date}.json`
- `data/config/agent_preferences.json`
- `data/config/screening_criteria.json`

**ChromaDB/LanceDB** (Vector Store):

- Earnings transcripts embeddings
- Historical research notes
- Pattern library (similar market conditions)
- Semantic search across past analyses

**Data Flow:**

1. Python scripts fetch from APIs (FRED, yfinance)
2. Cache raw responses to JSON
3. Process and store structured results in SQLite
4. Generate embeddings for semantic search
5. Frontend queries SQLite for dashboard
6. Agents query vector DB for context-aware research

## Tech Stack Summary

### **Frontend Layer**

- **Next.js 14+** - App router, server components
- **TypeScript** - Type safety throughout
- **TailwindCSS** - Styling
- **shadcn/ui** - Component primitives
- **Recharts/TradingView** - Charting
- **SWR** - Data fetching/caching

### **Orchestration Layer**

- **Node.js** - Agent coordination
- **Anthropic SDK** - Claude API calls
- **LangChain.js** (optional) - Agent framework if needed
- **Zod** - Schema validation

### **Analytics Layer**

- **Python 3.11+** - Core analytics
- **FastAPI** - Minimal HTTP wrapper
- **pandas** - Data manipulation
- **scikit-learn** - ML models
- **yfinance** - Market data
- **pytrends** - Google Trends
- **requests** - API calls

### **Data Layer**

- **SQLite** - Structured storage
- **ChromaDB/LanceDB** - Vector embeddings
- **JSON** - Config/cache

### **Infrastructure**

- **Electron** - Desktop wrapper
- **electron-builder** - Packaging
- **concurrently** - Dev process management

## Agent Communication Protocol

**Standardized Message Format:**

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

**Example Workflow:**

```
User: "Find undervalued opportunities in boring businesses"

1. Orchestrator → ScreeningAgent
   Request: { agent: 'screening', task: 'boring_business_scan' }
   Response: { data: [...20 stocks...], sources: ['yfinance', 'finviz'] }

2. Orchestrator → FundamentalAnalystAgent (for each)
   Request: { agent: 'fundamental', task: 'analyze_stock', context: {stock: 'XYZ'} }
   Python calls: earnings data, balance sheet, cash flow
   Claude synthesis: Business quality assessment
   Response: { data: {...analysis...}, reasoning: "...", confidence: 75 }

3. Orchestrator → DevilsAdvocateAgent (top 5)
   Request: { agent: 'devils_advocate', task: 'challenge_thesis', context: {...} }
   Claude: Identify risks, bear cases
   Response: { reasoning: "Three key risks: ...", confidence: 80 }

4. Final synthesis (Orchestrator calls Claude)
   Combine all agent outputs into coherent recommendation
```

## Development Workflow

**Iterative Module Building:**

**Week 1-2: Core Infrastructure**

- Set up Electron + Next.js shell
- Create Python FastAPI wrapper
- Build 3-5 core analytics modules
- Test each module independently

**Week 3-4: First Agents**

- Implement MarketRegimeAgent (calls CMDS, FRS, VP)
- Implement ScreeningAgent (calls screening scripts)
- Build basic chat interface
- Connect agents to frontend

**Week 5-6: Research Agents**

- Add FundamentalAnalystAgent
- Add DevilsAdvocateAgent
- Implement vector DB for context
- Multi-step agent workflows

**Week 7-8: Risk & Portfolio**

- Position sizing logic
- Portfolio tracking
- Alert system
- Historical backtesting

**Ongoing: Expand Analytics**

- Each week add 2-3 new Python modules
- Modules are independent, incremental value
- Agent orchestrator automatically discovers new capabilities

**Testing Pattern:**

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

## Key Advantages of This Design

**Modularity:**

- Python scripts are pure functions, completely independent
- Add new analytics without touching existing code
- Test each piece in isolation

**Scalability:**

- Start simple (5 agents, 10 Python modules)
- Expand incrementally (50+ agents, 100+ modules)
- Agent orchestrator handles complexity

**Maintainability:**

- Clear separation of concerns
- Each layer has single responsibility
- Easy to debug (check Python output, then agent logic, then UI)

**Flexibility:**

- Chat interface adapts to new agents automatically
- Dashboard widgets can tap into same agent system
- Python modules work via CLI, HTTP, or direct import

**Intelligence:**

- Claude agents provide synthesis across data sources
- Vector DB enables learning from past research
- Multi-agent collaboration for complex questions

## Example User Interaction

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

The system feels conversational but is backed by rigorous quantitative analysis at every step.


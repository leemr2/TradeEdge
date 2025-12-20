# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradeEdge is an AI-powered investment command center that combines fundamental risk analysis, volatility prediction, and market monitoring. The system uses a modular Python analytics backend with a Next.js frontend to provide retail investors with institutional-grade market analysis.

**Core Concept**: Three complementary scoring systems:
- **FRS (Fundamental Risk Score)**: 12-18 month strategic risk assessment (0-100)
- **VP (Volatility Predictor)**: 2-5 day tactical warning signals (0-100)
- **CMDS (Combined Market Danger Score)**: Unified signal = (0.65 × FRS) + (0.35 × VP)

## Architecture

### High-Level Structure

```
Frontend (Next.js/React) ↔ FastAPI Backend ↔ Python Analytics Modules ↔ Data Layer
```

**Key Design Principle**: Each Python analytics module is a **pure function** - takes input, returns JSON output. No shared state. No inter-module dependencies. Each module can be tested standalone via CLI before integration.

### Technology Stack

**Backend**:
- Python 3.11+ with FastAPI for HTTP API
- Modular analytics scripts in `backend/analytics/`
- Data fetchers: Alpha Vantage (primary), FRED API, Yahoo Finance (fallback)
- Local caching in `data/cache/`

**Frontend**:
- Next.js 16 with App Router
- TypeScript + React 19
- TailwindCSS 4 for styling
- Recharts for visualizations
- SWR for data fetching

**Data Storage**:
- SQLite (planned for structured data)
- JSON files for cache and configuration
- ChromaDB/LanceDB (planned for vector embeddings)

## Common Development Commands

### Backend

**Start the API server** (from `backend/` directory):
```bash
# Windows
python -m uvicorn api.main:app --reload

# Linux/Mac
uvicorn api.main:app --reload
```

**Test individual modules** (from `backend/` directory):
```bash
# Test Volatility Predictor
python -m analytics.core.volatility_predictor --mode json

# Test FRS Calculator (full calculation with all categories)
python -m analytics.core.frs_calculator

# Test CMDS Calculator
python -m analytics.core.cmds_calculator

# Test all modules
python scripts/test_all_modules.py
```

**Train VP model** (required on first setup, then weekly):
```bash
python -m analytics.core.volatility_predictor --mode train
# Or use script:
python scripts/train_vp_model.py
```

**Run backend tests**:
```bash
cd backend
pytest tests/

# Test specific category
pytest tests/test_frs_categories.py::test_macro_cycle

# Test with verbose output
pytest tests/ -v
```

### Frontend

**Start development server** (from `frontend/` directory):
```bash
npm run dev
```

**Build for production**:
```bash
npm run build
npm run start
```

**Lint frontend code**:
```bash
npm run lint
```

## Critical Architecture Patterns

### Python Module Design Pattern

Every analytics module in `backend/analytics/` follows this contract:

1. **Standalone CLI execution**: Must have a `main()` or `if __name__ == "__main__"` that outputs JSON to stdout
2. **Pure function**: No side effects, no shared state, deterministic output
3. **JSON output**: Always return structured JSON for easy testing and integration
4. **Local caching**: Each module caches its own data in `data/cache/`
5. **No inter-module dependencies**: Modules don't call other modules directly

**Example structure**:
```python
def calculate_something(param1, param2):
    """Core calculation logic."""
    # Fetch data (with caching)
    # Process data
    # Return result dict
    return {"score": 85, "components": {...}}

if __name__ == "__main__":
    result = calculate_something()
    print(json.dumps(result, indent=2))
```

### FRS Category System

The FRS (Fundamental Risk Score) uses a **modular category architecture** in `backend/analytics/core/categories/`:

- `base_category.py`: Abstract base class defining the category interface
- `macro_cycle.py`: Category 1 - Macro/Cycle indicators (0-30 points)
- `valuation.py`: Category 2 - Market valuation metrics (0-25 points)
- `leverage_stability.py`: Category 3 - Leverage & financial stability (0-25 points)
- `earnings_margins.py`: Category 4 - Earnings breadth/concentration (0-10 points)
- `sentiment.py`: Category 5 - Sentiment contrarian indicator (-10 to +10 points)

**Each category returns**:
- Category score (normalized to max points)
- Component breakdowns with individual scores
- Data freshness metadata (last_updated, next_update)
- Data source information

**Why this matters**: Categories can be improved/modified independently without breaking the overall FRS calculation. Each category is testable in isolation.

### Manual Inputs System

Some data (hedge fund leverage, CRE delinquency) isn't available via API and requires manual updates:

- Stored in `data/config/manual_inputs.json`
- Updated via API endpoint: `POST /api/frs/manual-inputs`
- Update schedule tracked in metadata
- Defaults provided on first run

**Update schedule**:
- Hedge fund leverage: Semi-annually (May, November) from Fed FSR
- CRE delinquency rate: Quarterly (~6 weeks after quarter end) from FDIC QBP

### Data Caching Strategy

All external API calls are cached locally to minimize API usage and improve performance:

```
data/cache/
├── fred/          # FRED API data (7-day TTL)
├── alphavantage/  # Alpha Vantage data (smart daily caching)
├── yfinance/      # Yahoo Finance data (24-hour TTL)
└── models/        # Trained ML models
```

**Cache files are named**: `{data_type}_{identifier}_{date}.json`

The caching logic is in `backend/analytics/data_fetchers/`:
- `fred_client.py`: FRED API with caching
- `alphavantage_client.py`: Alpha Vantage API with smart daily caching
- `yfinance_client.py`: Yahoo Finance with caching (fallback only)
- `market_data_manager.py`: Unified market data interface with intelligent routing

**Market Data Routing Strategy** (as of Dec 2025):
- **Primary source**: Alpha Vantage (free tier, 25 API calls/day)
- **Smart caching**: Only fetches if data through yesterday's close doesn't exist
- **Symbol mapping**: `^GSPC` → SPY proxy, `^VIX` → always Yahoo Finance
- **Automatic fallback**: Yahoo Finance if Alpha Vantage fails or budget exhausted
- **Budget tracking**: Monitored via `/api/budget` endpoint

## API Endpoints Reference

### Core Scores
- `GET /api/health` - Health check
- `GET /api/volatility` - Volatility Predictor score
- `GET /api/frs` - Fundamental Risk Score (includes full category breakdown)
- `GET /api/cmds` - Combined Market Danger Score
- `GET /api/cmds?frs_weight=0.7&vp_weight=0.3` - CMDS with custom weights

### Manual Inputs Management
- `GET /api/frs/manual-inputs` - Get current manual input values
- `POST /api/frs/manual-inputs` - Update manual inputs
  ```json
  {
    "hedge_fund_leverage": 10,
    "cre_delinquency_rate": 5.0,
    "as_of": "2025-12-09"
  }
  ```

### API Budget Monitoring
- `GET /api/budget` - Check Alpha Vantage API usage
  ```json
  {
    "used": 7,
    "limit": 25,
    "remaining": 18,
    "resets_at": "2025-12-20T00:00:00Z",
    "date": "2025-12-19"
  }
  ```

## Agent System (Planned)

The architecture is designed for future **agent-based orchestration**:

**Data Agents** (call Python scripts):
- MarketRegimeAgent: Calls CMDS, FRS, VP calculators
- ScreeningAgent: Stock screening modules
- RiskMonitorAgent: Portfolio exposure and systemic risk

**Research Agents** (use LLM synthesis):
- FundamentalAnalystAgent: Deep-dive stock analysis
- DevilsAdvocateAgent: Challenge investment thesis
- SentimentAnalystAgent: Aggregate sentiment signals

**Current state**: Agent orchestrator is **not yet implemented**. The modular Python architecture was designed to make future agent integration straightforward.

## Key Data Sources & Dependencies

### External APIs
- **Alpha Vantage**: Primary market data source (requires API key, free tier: 25 calls/day)
  - Get API key: https://www.alphavantage.co/support/#api-key
  - Used for: SPY, QQQ, RSP, IWM, KRE, and ^GSPC (via SPY proxy)
  - Smart daily caching minimizes API usage
- **FRED API**: Economic indicators (requires API key in environment variable `FRED_API_KEY`)
  - Get API key: https://fred.stlouisfed.org/docs/api/api_key.html
- **Yahoo Finance**: Fallback market data source (via yfinance library)
  - Used for: ^VIX (not available in Alpha Vantage free tier)
  - Fallback when Alpha Vantage fails or budget exhausted
- **Google Trends**: Search behavior data (via pytrends - planned for VP)

### Environment Setup
Backend requires environment variables in `backend/.env`:
```bash
FRED_API_KEY=your_fred_api_key_here
ALPHA_VANTAGE_API_KEY=your_alphavantage_api_key_here
```

**PowerShell (Windows) - temporary**:
```powershell
$env:FRED_API_KEY="your_fred_api_key_here"
$env:ALPHA_VANTAGE_API_KEY="your_alphavantage_api_key_here"
```

## Testing Strategy

### Unit Tests
Located in `backend/tests/`:
- `test_frs_calculator.py`: FRS calculation and category integration
- `test_cmds_calculator.py`: CMDS calculation logic

Run with: `pytest tests/` from `backend/` directory

### Integration Tests
Test the full stack:
1. Start backend: `python -m uvicorn api.main:app --reload`
2. Test API endpoints: `curl http://localhost:8000/api/frs`
3. Start frontend: `npm run dev` (from `frontend/`)
4. Verify UI displays scores correctly

### Module Testing Pattern
Each Python module can be tested standalone:
```bash
# Run module directly - should output JSON
python -m analytics.core.frs_calculator

# Verify output is valid JSON
python -m analytics.core.frs_calculator | python -m json.tool
```

## Common Gotchas

### Alpha Vantage Integration (Dec 2025)
The system now uses **Alpha Vantage as the primary market data source** with Yahoo Finance as fallback:

**Key points**:
- Free tier limit: 25 API calls/day (resets at midnight UTC)
- Smart caching: Only fetches if data through yesterday's close doesn't exist
- Typical usage: 6-7 calls on first run, 0 calls on subsequent same-day runs
- Symbol mapping: `^GSPC` uses SPY as proxy (indices not in free tier)
- VIX always uses Yahoo Finance (not available in Alpha Vantage free tier)

**Common issues**:
- **"No time series data in response"**: Using wrong endpoint or API key not set
  - Solution: Verify `ALPHA_VANTAGE_API_KEY` in `.env`, ensure using free tier endpoint
- **"API budget exhausted"**: Exceeded 25 calls/day
  - Solution: System auto-falls back to Yahoo Finance, budget resets at midnight UTC
- **"^GSPC not found"**: Free tier doesn't support indices
  - Solution: System automatically uses SPY as proxy (they track closely)

See `ALPHA_VANTAGE_INTEGRATION_2025-12-19.md` for complete details.

### yfinance Data Access (Fallback Only)
Yahoo Finance is now used primarily as a fallback. The codebase includes error handling in `yfinance_client.py`. Recent fixes (Dec 2025) addressed:
- Forward P/E ratio access issues
- Ticker info access with retries
- Proper fallback to historical P/E when forward P/E unavailable

See `YFINANCE_FIXES_2025-12-18.md` for details.

### Manual Inputs Initialization
On first run, `manual_inputs.json` must be created with default values. The system auto-creates defaults, but verify the file exists in `data/config/manual_inputs.json`.

### Python Module Imports
When running modules from CLI, use the `-m` flag and module path notation:
```bash
# Correct
python -m analytics.core.frs_calculator

# Wrong (will fail with import errors)
python analytics/core/frs_calculator.py
```

### Alpha Vantage API Budget
Alpha Vantage free tier allows 25 API calls/day:
- Monitor usage via `/api/budget` endpoint
- Smart daily caching minimizes calls (only fetches missing data)
- System automatically falls back to Yahoo Finance if budget exhausted
- Budget resets at midnight UTC
- Typical weekly usage: 6-7 calls total (well under limit)

### FRED API Rate Limits
FRED has generous rate limits but caching is essential. Cache TTL is 7 days for FRED data. Don't disable caching unless testing data freshness.

## File Organization Conventions

### Python Code Structure
```
backend/
├── analytics/          # Analytics modules (the "brains")
│   ├── core/          # Core scoring systems
│   │   ├── categories/  # FRS category modules
│   │   ├── frs_calculator.py
│   │   ├── cmds_calculator.py
│   │   └── volatility_predictor.py
│   ├── data_fetchers/  # API wrappers with caching
│   │   ├── alphavantage_client.py    # Primary market data source
│   │   ├── yfinance_client.py        # Fallback market data
│   │   ├── fred_client.py            # Economic data
│   │   └── market_data_manager.py    # Unified routing interface
│   └── utils/         # Shared utilities
│       └── api_budget_tracker.py     # Alpha Vantage budget tracking
├── api/               # FastAPI application
├── tests/             # Unit and integration tests
└── scripts/           # Utility scripts (training, testing)
```

### Frontend Structure
```
frontend/
├── app/               # Next.js App Router pages
│   ├── page.tsx      # Main dashboard
│   └── admin/        # Admin pages (manual inputs)
├── components/        # React components
│   ├── FRSDisplay.tsx
│   ├── CategoryCard.tsx
│   ├── ManualInputEditor.tsx
│   └── ...
└── lib/              # Utilities and API client
    └── api.ts        # Backend API client
```

### Data Directory
```
data/
├── cache/            # Cached API responses
│   ├── fred/         # FRED economic data (7-day TTL)
│   ├── alphavantage/ # Alpha Vantage market data (smart daily caching)
│   ├── yfinance/     # Yahoo Finance fallback data (24-hour TTL)
│   └── models/       # Trained ML models
└── config/           # Configuration files
    └── manual_inputs.json
```

## Making Changes to FRS Categories

If you need to modify or add FRS category logic:

1. **Understand the base class**: Review `base_category.py` for the interface contract
2. **Modify category module**: Edit the specific category file (e.g., `macro_cycle.py`)
3. **Test in isolation**: Run the category calculation directly in Python REPL
4. **Test via FRS calculator**: `python -m analytics.core.frs_calculator`
5. **Verify API response**: `curl http://localhost:8000/api/frs`
6. **Check frontend rendering**: Ensure UI displays updated data correctly

Categories are **loosely coupled** - changes to one category don't affect others.

## Adding New Analytics Modules

To add a new analytics module (e.g., a new stock screener):

1. Create module in appropriate directory (e.g., `backend/analytics/screening/`)
2. Follow the pure function pattern: input parameters → JSON output
3. Add `if __name__ == "__main__"` block for CLI testing
4. Implement local caching for any external data fetches
5. Add unit tests in `backend/tests/`
6. Optionally expose via FastAPI in `api/main.py`

**Example skeleton**:
```python
# backend/analytics/screening/my_screener.py
import json

def screen_stocks(criteria: dict) -> dict:
    """Screen stocks based on criteria."""
    # Fetch data (with caching)
    # Apply filters
    # Return results
    return {
        "results": [...],
        "count": len(...),
        "criteria": criteria
    }

if __name__ == "__main__":
    result = screen_stocks({"min_roe": 15})
    print(json.dumps(result, indent=2))
```

## Performance Considerations

- **API call minimization**: Caching is critical - don't bypass it
- **Parallel data fetching**: When multiple API calls are needed, fetch in parallel (not yet implemented, but architecture supports it)
- **Frontend data refresh**: Use SWR with appropriate revalidation intervals (currently configured per component)

## Security Notes

- **API keys**: Never commit `FRED_API_KEY` or other secrets. Use environment variables or `.env` files (which are gitignored)
- **Local-first design**: All data stored locally for privacy - no external database
- **No user authentication yet**: Current implementation assumes single-user desktop application

## Future Planned Features

Based on PRD.md and architecture docs:

1. **Agent orchestration layer**: Multi-agent workflows for complex analysis
2. **Portfolio tracking**: SQLite database for positions, trades, P&L
3. **Stock screening modules**: Value/Quality/Momentum, turnaround detection
4. **Technical analysis**: Trend analysis, support/resistance
5. **Alert system**: Push notifications for CMDS zone changes
6. **Electron desktop app**: Package as standalone desktop application
7. **Vector DB integration**: ChromaDB/LanceDB for semantic search of research

These are **not yet implemented** - the current codebase focuses on the core scoring systems (FRS, VP, CMDS).

## Documentation References

- `PRD.md`: Full product requirements and vision
- `TradeEdge High-Level Architecture.md`: System design overview
- `backend/README.md`: Backend-specific setup and API documentation
- `README.md`: Quick start guide
- `SETUP_WINDOWS.md`: Windows-specific setup instructions
- `backend/FRS Category Reference Guide.md`: Detailed FRS category documentation
- `ALPHA_VANTAGE_INTEGRATION_2025-12-19.md`: Alpha Vantage integration details and architecture
- `YFINANCE_FIXES_2025-12-18.md`: Yahoo Finance fallback fixes

## When Working on This Codebase

1. **Test modules standalone first**: Always run Python modules via CLI before testing via API
2. **Respect the module boundaries**: Don't create dependencies between analytics modules
3. **Cache everything**: External API calls should always be cached
4. **Maintain JSON output**: All analytics modules must output valid JSON
5. **Update manual inputs metadata**: When adding new manual inputs, update the schema and documentation
6. **Category independence**: FRS categories should remain independent and testable in isolation
7. **Document major changes**: When making significant architectural changes, update relevant documentation files (see Documentation Maintenance below)

## Common Development Workflows

### Adding a New Data Source
1. Create client in `backend/analytics/data_fetchers/`
2. Implement caching logic (follow pattern in `alphavantage_client.py`)
3. Add routing logic to `market_data_manager.py` if it's a market data source
4. Add to existing modules or create new module
5. Test caching behavior (check `data/cache/`)
6. If API has rate limits, add budget tracking (see `api_budget_tracker.py`)

### Modifying FRS Calculation
1. Identify which category needs change
2. Edit category module in `backend/analytics/core/categories/`
3. Test category: `python -c "from analytics.core.categories.X import XCategory; ..."`
4. Test full FRS: `python -m analytics.core.frs_calculator`
5. Verify API: `curl http://localhost:8000/api/frs`

### Adding New API Endpoint
1. Edit `backend/api/main.py`
2. Add route function
3. Call appropriate analytics module(s)
4. Return JSON response
5. Test: `curl http://localhost:8000/api/your-endpoint`
6. Add frontend API client function in `frontend/lib/api.ts`

### Creating New Frontend Component
1. Add component in `frontend/components/`
2. Use TypeScript with proper types
3. Fetch data via `frontend/lib/api.ts` functions
4. Use SWR for data fetching/caching
5. Style with TailwindCSS
6. Integrate into page in `frontend/app/`

## Documentation Maintenance

**IMPORTANT**: When making significant changes to the codebase, update the relevant documentation to keep it synchronized with the actual implementation.

### What Constitutes a "Major Change"?

Update documentation when you:
- **Add/remove/modify data sources** (e.g., new API integrations, changing primary data provider)
- **Change architecture patterns** (e.g., new caching strategy, routing logic, module organization)
- **Add/modify core features** (e.g., new scoring categories, calculation formulas, API endpoints)
- **Change environment requirements** (e.g., new API keys, dependencies, configuration files)
- **Fix significant bugs** that reveal important gotchas or usage patterns
- **Add new modules or major components** (e.g., new analytics modules, agent types)
- **Modify file organization** (e.g., restructuring directories, renaming key files)

### Documentation Update Checklist

When you make a major change, review and update these files as appropriate:

#### Always Update:
- **CLAUDE.md** (this file) - Update relevant sections:
  - Technology Stack if dependencies changed
  - API Endpoints if new endpoints added
  - Common Gotchas if you discovered new issues
  - Common Development Workflows if process changed
  - External APIs section if data sources changed
  - File Organization if structure changed

#### Frequently Update:
- **README.md** - User-facing quick start and setup
  - Update setup instructions if environment requirements changed
  - Update API endpoint list if new endpoints added
  - Update testing commands if test structure changed

- **backend/README.md** - Backend-specific documentation
  - Update if API endpoints changed
  - Update if testing procedures changed
  - Update if module architecture changed

#### Create New Documentation When:
- **Major integration/refactoring** - Create dated markdown file (e.g., `INTEGRATION_NAME_YYYY-MM-DD.md`)
  - Document what changed, why, and how to use it
  - Include troubleshooting section
  - List all modified files
  - Provide testing instructions

- **Complex bug fixes** - Document in dated file (e.g., `BUG_FIX_DESCRIPTION_YYYY-MM-DD.md`)
  - Explain the issue, root cause, and solution
  - Include prevention strategies

#### Conditional Updates:
- **.cursorrules** - Update if coding standards or patterns changed
- **PRD.md** - Only if product vision/requirements fundamentally changed (rare)
- **Architecture.md** - Only if system design patterns changed

### Documentation Update Process

1. **During development**: Keep notes of what you changed and why
2. **Before committing**: Review the Documentation Update Checklist above
3. **Update relevant files**: Make targeted updates to each affected document
4. **Add references**: Cross-reference new documentation in CLAUDE.md's "Documentation References" section
5. **Test documentation**: Verify commands and examples in documentation still work
6. **Be specific**: Include file names, function names, and concrete examples

### Good Documentation Update Examples

**Example 1: Adding Alpha Vantage Integration**
- ✅ Created `ALPHA_VANTAGE_INTEGRATION_2025-12-19.md` with full details
- ✅ Updated CLAUDE.md: Technology Stack, Data Caching Strategy, API Endpoints, External APIs, Common Gotchas
- ✅ Updated README.md: Environment setup, testing commands
- ✅ Updated backend/README.md: API endpoints, testing procedures
- ✅ Added documentation reference to CLAUDE.md

**Example 2: Fixing yfinance Data Access**
- ✅ Created `YFINANCE_FIXES_2025-12-18.md` documenting the issue and solution
- ✅ Updated CLAUDE.md: Common Gotchas section
- ✅ Added documentation reference

**Example 3: Adding New FRS Category**
- ✅ Update CLAUDE.md: FRS Category System section
- ✅ Update backend/README.md: Module testing examples
- ✅ Update backend/FRS Category Reference Guide.md: Category details
- ✅ Update .cursorrules: FRS Component Scoring if formula changed

### Documentation Quality Standards

- **Be concise**: Focus on what changed and how to use it
- **Be specific**: Include file paths, function names, and code examples
- **Be current**: Include dates and version information
- **Be practical**: Focus on actionable information developers need
- **Cross-reference**: Link related documentation sections
- **Test your docs**: Verify commands and examples actually work

### Don't Document

- Obvious implementation details easily discovered by reading code
- Every single file in the codebase
- Generic development best practices unrelated to this project
- Temporary debugging code or experimental features
- Information that will quickly become outdated (use comments in code instead)

---

**Remember**: Good documentation is a force multiplier. Future Claude instances (and your future self) will thank you for keeping documentation synchronized with the actual codebase.

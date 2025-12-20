# TradeEdge: AI-Powered Investment Command Center

A personal investment tool that provides proactive insights, risk monitoring, and AI-augmented research to support independent investment decisions.

## Overview

TradeEdge combines:
- **Fundamental Risk Score (FRS)**: 12-18 month strategic risk assessment
- **Volatility Predictor (VP)**: 2-5 day tactical warning signals
- **Combined Market Danger Score (CMDS)**: Unified signal driving allocation decisions

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- FRED API key (get from https://fred.stlouisfed.org/docs/api/api_key.html)
- Alpha Vantage API key (get free key from https://www.alphavantage.co/support/#api-key)

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables:

**Option 1: PowerShell (Windows) - Current Session Only:**
```powershell
$env:FRED_API_KEY="your_fred_api_key_here"
```

**Option 2: PowerShell (Windows) - Permanent:**
```powershell
[System.Environment]::SetEnvironmentVariable('FRED_API_KEY', 'your_fred_api_key_here', 'User')
```

**Option 3: Create .env file (Recommended):**
Create a `.env` file in the `backend/` directory:
```
FRED_API_KEY=your_fred_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
```

Then install python-dotenv (already in requirements.txt) and the code will automatically load it.

**Note:** Alpha Vantage free tier provides 25 API calls per day. The system intelligently caches data and only fetches when needed, staying well within this limit.

3. Train the Volatility Predictor model (first time only):
```bash
python -m analytics.core.volatility_predictor --mode train
# Or use the script:
python scripts/train_vp_model.py
```

4. Start the FastAPI backend:

**Windows PowerShell:**
```powershell
cd backend
python -m uvicorn api.main:app --reload
# Or use the helper script:
.\start_server.ps1
```

**Linux/Mac:**
```bash
cd backend
uvicorn api.main:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Project Structure

```
tradeedge/
├── backend/
│   ├── analytics/
│   │   ├── core/
│   │   │   ├── volatility_predictor.py  # VP calculator
│   │   │   ├── frs_calculator.py        # FRS calculator (orchestrator)
│   │   │   ├── cmds_calculator.py       # CMDS calculator
│   │   │   ├── manual_inputs.py         # Manual input manager
│   │   │   └── categories/             # Modular FRS categories
│   │   │       ├── base_category.py     # Abstract base class
│   │   │       ├── macro_cycle.py       # Category 1: Macro/Cycle
│   │   │       ├── valuation.py         # Category 2: Valuation
│   │   │       ├── leverage_stability.py # Category 3: Leverage & Stability
│   │   │       ├── earnings_margins.py   # Category 4: Earnings & Margins
│   │   │       └── sentiment.py         # Category 5: Sentiment
│   │   └── data_fetchers/
│   │       ├── fred_client.py          # FRED API wrapper
│   │       ├── alphavantage_client.py  # Alpha Vantage API wrapper (primary)
│   │       ├── yfinance_client.py      # Yahoo Finance wrapper (fallback)
│   │       └── market_data_manager.py  # Unified data source manager
│   │   └── utils/
│   │       └── api_budget_tracker.py   # API call budget tracking
│   ├── api/
│   │   └── main.py                     # FastAPI application
│   ├── tests/                          # Unit tests
│   └── scripts/                        # Utility scripts
├── frontend/
│   ├── app/                            # Next.js app router
│   ├── components/                     # React components
│   │   ├── FRSDisplay.tsx              # Main FRS display
│   │   ├── CategoryCard.tsx            # Expandable category cards
│   │   ├── ComponentDetail.tsx         # Component breakdown
│   │   └── ManualInputEditor.tsx       # Manual input editor
│   └── lib/                           # Utilities & API client
└── data/
    ├── cache/                         # Cached API data
    └── config/                        # Configuration files
        └── manual_inputs.json         # Manual input values
```

## Testing Individual Modules

Each Python module can be run standalone:

```bash
# Volatility Predictor
python -m analytics.core.volatility_predictor --mode json

# FRS Calculator (full calculation with all categories)
python -m analytics.core.frs_calculator

# CMDS Calculator
python -m analytics.core.cmds_calculator

# Test all modules
python scripts/test_all_modules.py
```

### Testing FRS Categories Individually

The FRS calculator is now modular. Test individual categories:

```python
# Example: Test Macro/Cycle category
from analytics.data_fetchers.fred_client import FredClient
from analytics.data_fetchers.market_data_manager import MarketDataManager
from analytics.core.categories.macro_cycle import MacroCycleCategory
from analytics.core.manual_inputs import load_manual_inputs

fred = FredClient()
market_data = MarketDataManager()  # Uses Alpha Vantage primary, Yahoo fallback
manual_inputs = load_manual_inputs()

macro = MacroCycleCategory(fred_client=fred, market_data=market_data, manual_inputs=manual_inputs)
result = macro.calculate()
print(result)
```

## API Endpoints

### Core Endpoints
- `GET /api/health` - Health check
- `GET /api/volatility` - Get VP score
- `GET /api/frs` - Get FRS score (includes detailed category breakdowns)
- `GET /api/cmds` - Get CMDS score
- `GET /api/cmds?frs_weight=0.7&vp_weight=0.3` - Custom weights

### Manual Inputs Management
- `GET /api/frs/manual-inputs` - Get current manual input values
- `POST /api/frs/manual-inputs` - Update manual input values
  ```json
  {
    "hedge_fund_leverage": 10,
    "cre_delinquency_rate": 5.0,
    "as_of": "2025-12-09"
  }
  ```

### API Budget Monitoring
- `GET /api/budget` - Get Alpha Vantage API call usage for today
  Returns: `{used: int, limit: 25, remaining: int, resets_at: string}`

## Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Testing FRS Categories

The FRS calculator is modular - test individual categories:

```bash
# Run unit tests for categories
pytest tests/test_frs_categories.py

# Test specific category
pytest tests/test_frs_categories.py::test_macro_cycle

# Test manual inputs
pytest tests/test_manual_inputs.py
```

### Manual Input Management

Manual inputs are stored in `data/config/manual_inputs.json` and can be updated:

**Via API:**
```bash
curl -X POST http://localhost:8000/api/frs/manual-inputs \
  -H "Content-Type: application/json" \
  -d '{"hedge_fund_leverage": 10, "cre_delinquency_rate": 5.0}'
```

**Via File:**
Edit `data/config/manual_inputs.json` directly. Values will be loaded on next FRS calculation.

**Update Schedule:**
- **Hedge Fund Leverage**: Update semi-annually (May, November) from Fed Financial Stability Report
- **CRE Delinquency**: Update quarterly (~6 weeks after quarter end) from FDIC Quarterly Banking Profile

### Training VP Model

The Volatility Predictor model should be retrained weekly:

```bash
python scripts/train_vp_model.py
```

### Data Sources & Caching

TradeEdge uses a smart multi-source data fetching strategy:

**Primary Data Source: Alpha Vantage**
- Free tier: 25 API calls/day
- Used for: SPY, QQQ, RSP, IWM, KRE, ^GSPC (via SPY proxy)
- Cache: `data/cache/alphavantage/` (daily, checks for yesterday's close)
- Budget tracking: Automatically tracks daily API usage

**Fallback Data Source: Yahoo Finance**
- Used for: ^VIX (not available in Alpha Vantage free tier)
- Fallback: If Alpha Vantage fails or budget exhausted
- Cache: `data/cache/yfinance/` (24-hour TTL)

**Other Data Sources:**
- FRED API: Economic indicators (`data/cache/fred/`, 7-day TTL)
- Google Trends: Sentiment data (cached)
- Trained models: `data/cache/models/`
- Configuration: `data/config/manual_inputs.json`

**Smart Caching Logic:**
- Checks if data through yesterday's close exists before fetching
- Only fetches new data when needed (perfect for weekly usage)
- Falls back to Yahoo Finance if Alpha Vantage unavailable
- Uses stale cache with warning if both sources fail

### FRS Category Architecture

The FRS calculator uses a modular architecture with 5 independent categories:

1. **Macro/Cycle** (0-30 points): Unemployment, yield curve, GDP growth
2. **Valuation** (0-25 points): Forward P/E, Buffett Indicator, equity yield vs T-bills
3. **Leverage & Stability** (0-25 points): Hedge fund leverage, corporate credit, CRE stress
4. **Earnings & Margins** (0-10 points): Earnings breadth (concentration)
5. **Sentiment** (-10 to +10 points): VIX-based contrarian indicator

Each category:
- Can be tested independently
- Returns detailed component breakdowns
- Includes metadata (update frequency, data sources, next update dates)
- Can be improved without affecting other categories

See `backend/FRS Category Reference Guide.md` for complete documentation.

## Architecture

- **Modular Python "Brains"**: Each analytics module is independent and outputs JSON
- **FastAPI Backend**: HTTP wrapper around Python modules
- **Next.js Frontend**: React dashboard with real-time data visualization
- **Local-First**: All data cached locally for privacy and speed
- **Smart Data Fetching**: Alpha Vantage primary with Yahoo Finance fallback, intelligent daily caching

## License

This project is for personal/educational use.

## Disclaimer

This is a decision-support tool, not financial advice. Past performance doesn't guarantee future results. Always use proper risk management and never risk more than you can afford to lose.


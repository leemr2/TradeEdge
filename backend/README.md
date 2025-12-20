# TradeEdge Backend

Python analytics backend for TradeEdge investment command center.

## Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys:
# FRED_API_KEY=your_fred_api_key_here
# ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
```

**Get API Keys:**
- FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
- Alpha Vantage API key: https://www.alphavantage.co/support/#api-key (free tier: 25 calls/day)

3. Train the Volatility Predictor model (first time only):
```bash
python -m analytics.core.volatility_predictor --mode train
```

4. Initialize manual inputs configuration (first time only):
```bash
# Manual inputs will be auto-created with defaults on first run
# Or manually create/edit: data/config/manual_inputs.json
```

## Running the API

```bash
cd backend
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Core Endpoints
- `GET /` - API info
- `GET /api/health` - Health check
- `GET /api/volatility` - Get VP score
- `GET /api/frs` - Get FRS score (with detailed category breakdown)
- `GET /api/cmds` - Get CMDS score
- `GET /api/cmds?frs_weight=0.7&vp_weight=0.3` - Get CMDS with custom weights

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

## FRS Architecture

The FRS calculator is now modular with 5 independent category modules:

```
backend/analytics/core/
├── frs_calculator.py          # Main orchestrator
├── manual_inputs.py            # Manual input manager
└── categories/
    ├── base_category.py       # Abstract base class
    ├── macro_cycle.py         # Category 1: Macro/Cycle (0-30 pts)
    ├── valuation.py            # Category 2: Valuation (0-25 pts)
    ├── leverage_stability.py  # Category 3: Leverage & Stability (0-25 pts)
    ├── earnings_margins.py    # Category 4: Earnings & Margins (0-10 pts)
    └── sentiment.py           # Category 5: Sentiment (-10 to +10 pts)
```

Each category module:
- Is independently testable
- Returns detailed component breakdowns
- Includes metadata (update frequency, data sources, next update dates)
- Can be improved/modified without affecting other categories

## Testing Individual Modules

### Full FRS Calculator
```bash
# Run complete FRS calculation
python -m analytics.core.frs_calculator

# Output includes:
# - Overall FRS score
# - Category breakdowns
# - Component-level details
# - Manual inputs status
```

### Individual Category Testing

Each category can be tested independently:

```python
# Example: Test Macro/Cycle category
from analytics.data_fetchers.fred_client import FredClient
from analytics.data_fetchers.market_data_manager import MarketDataManager
from analytics.core.categories.macro_cycle import MacroCycleCategory
from analytics.core.manual_inputs import load_manual_inputs

fred = FredClient()
market_data = MarketDataManager()  # Uses Alpha Vantage primary, Yahoo fallback
manual_inputs = load_manual_inputs()

macro = MacroCycleCategory(
    fred_client=fred,
    market_data=market_data,
    manual_inputs=manual_inputs
)

result = macro.calculate()
print(result)
```

### Other Modules
```bash
# Volatility Predictor
python -m analytics.core.volatility_predictor --mode json

# CMDS Calculator
python -m analytics.core.cmds_calculator
```

## Testing Protocols

### Unit Testing

Run all tests:
```bash
cd backend
pytest tests/
```

Test specific category:
```bash
pytest tests/test_frs_categories.py::test_macro_cycle
```

### Integration Testing

1. **Test FRS Calculation Flow:**
   ```bash
   # 1. Test individual categories
   python -c "from analytics.core.categories.macro_cycle import MacroCycleCategory; ..."
   
   # 2. Test full FRS calculator
   python -m analytics.core.frs_calculator
   
   # 3. Test API endpoint
   curl http://localhost:8000/api/frs
   ```

2. **Test Manual Inputs:**
   ```bash
   # Get current values
   curl http://localhost:8000/api/frs/manual-inputs
   
   # Update values
   curl -X POST http://localhost:8000/api/frs/manual-inputs \
     -H "Content-Type: application/json" \
     -d '{"hedge_fund_leverage": 10, "cre_delinquency_rate": 5.0}'
   
   # Verify update
   curl http://localhost:8000/api/frs/manual-inputs
   ```

3. **Test Data Freshness:**
   ```bash
   # Check component timestamps in FRS response
   python -m analytics.core.frs_calculator | jq '.categories.macro_cycle.components'
   ```

### Manual Input Management

Manual inputs are stored in `data/config/manual_inputs.json`:

```json
{
  "hedge_fund_leverage": 10,
  "hedge_fund_leverage_as_of": "2025-11-01",
  "cre_delinquency_rate": 5.0,
  "cre_delinquency_as_of": "2025-11-15"
}
```

**Update Schedule:**
- **Hedge Fund Leverage**: Semi-annually (May, November) from Fed FSR
- **CRE Delinquency**: Quarterly (~6 weeks after quarter end) from FDIC QBP

**Update via API:**
```bash
curl -X POST http://localhost:8000/api/frs/manual-inputs \
  -H "Content-Type: application/json" \
  -d '{
    "hedge_fund_leverage": 10,
    "cre_delinquency_rate": 8.5,
    "as_of": "2025-12-09"
  }'
```

**Update via File:**
Edit `data/config/manual_inputs.json` directly (will be loaded on next FRS calculation).

## Data Sources & Caching

### Primary: Alpha Vantage
- **Free tier**: 25 API calls/day
- **Used for**: SPY, QQQ, RSP, IWM, KRE, ^GSPC (via SPY proxy)
- **Cache**: `data/cache/alphavantage/` (smart daily caching - checks for yesterday's close)
- **Budget tracking**: Automatically tracks daily API usage
- **Endpoint**: `TIME_SERIES_DAILY` (free tier)

### Fallback: Yahoo Finance
- **Used for**: ^VIX (not available in Alpha Vantage free tier)
- **Fallback**: If Alpha Vantage fails or budget exhausted
- **Cache**: `data/cache/yfinance/` (24-hour TTL)

### Other Data Sources
- **FRED API**: Economic indicators (`data/cache/fred/`, 7-day TTL)
- **Google Trends**: Sentiment data (cached)
- **Trained models**: `data/cache/models/`
- **Configuration**: `data/config/manual_inputs.json`

### Smart Caching Logic
- Checks if data through **yesterday's close** exists before fetching
- Only fetches new data when needed (perfect for weekly usage)
- Falls back to Yahoo Finance if Alpha Vantage unavailable
- Uses stale cache with warning if both sources fail

### API Budget Management
Monitor daily API usage:
```bash
curl http://localhost:8000/api/budget
```

Typical usage: 6-7 calls/day (well under 25 limit)

## Category Update Frequencies

| Category | Update Frequency | Data Sources |
|----------|-----------------|--------------|
| Macro/Cycle | Mixed | FRED (monthly/daily/quarterly) |
| Valuation | Daily/Quarterly | Alpha Vantage (primary), Yahoo Finance (fallback), FRED |
| Leverage & Stability | Daily/Semi-annual/Quarterly | Alpha Vantage (primary), FRED, Manual (Fed FSR, FDIC) |
| Earnings & Margins | Real-time | Alpha Vantage (primary), Yahoo Finance (fallback) |
| Sentiment | Real-time | Yahoo Finance (VIX only) |

**Data Source Priority:**
1. **Alpha Vantage** - Primary for SPY, QQQ, RSP, IWM, KRE, ^GSPC
2. **Yahoo Finance** - Primary for ^VIX, fallback for others
3. **FRED** - Economic indicators (unemployment, yield curve, GDP, etc.)

See `backend/FRS Category Reference Guide.md` for detailed update schedules and data source information.

## Data Fetcher Architecture

```
backend/analytics/data_fetchers/
├── fred_client.py              # FRED API wrapper
├── alphavantage_client.py      # Alpha Vantage API wrapper (primary)
├── yfinance_client.py          # Yahoo Finance wrapper (fallback)
└── market_data_manager.py      # Unified data source manager
```

The `MarketDataManager` provides a unified interface that:
- Routes ^VIX requests to Yahoo Finance
- Uses Alpha Vantage for all other tickers
- Automatically falls back to Yahoo Finance if Alpha Vantage fails
- Implements smart daily caching (checks for yesterday's close)
- Tracks API budget usage


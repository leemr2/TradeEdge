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
# Edit .env and add your FRED_API_KEY
```

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
from analytics.data_fetchers.yfinance_client import YFinanceClient
from analytics.core.categories.macro_cycle import MacroCycleCategory
from analytics.core.manual_inputs import load_manual_inputs

fred = FredClient()
yfinance = YFinanceClient()
manual_inputs = load_manual_inputs()

macro = MacroCycleCategory(
    fred_client=fred,
    yfinance_client=yfinance,
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

## Data Caching

All data is cached locally in `data/cache/`:
- FRED data: `data/cache/fred/` (7-day TTL)
- Yahoo Finance data: `data/cache/yfinance/` (24-hour TTL)
- Trained models: `data/cache/models/`
- Configuration: `data/config/manual_inputs.json`

## Category Update Frequencies

| Category | Update Frequency | Data Sources |
|----------|-----------------|--------------|
| Macro/Cycle | Mixed | FRED (monthly/daily/quarterly) |
| Valuation | Daily/Quarterly | Yahoo Finance, FRED |
| Leverage & Stability | Daily/Semi-annual/Quarterly | FRED, Manual (Fed FSR, FDIC) |
| Earnings & Margins | Real-time | Yahoo Finance |
| Sentiment | Real-time | Yahoo Finance (VIX) |

See `backend/FRS Category Reference Guide.md` for detailed update schedules and data source information.


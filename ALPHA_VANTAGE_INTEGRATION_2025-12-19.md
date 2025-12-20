# Alpha Vantage Integration - December 19, 2025

## Overview

TradeEdge has been upgraded to use **Alpha Vantage** as the primary market data source, replacing the unreliable Yahoo Finance API for most tickers. This provides more reliable data access while staying within the free tier limit of 25 API calls per day.

## Architecture Changes

### Data Source Strategy

**Primary: Alpha Vantage**
- Free tier: 25 API calls/day
- Endpoint: `TIME_SERIES_DAILY` (free tier, not premium `TIME_SERIES_DAILY_ADJUSTED`)
- Used for: SPY, QQQ, RSP, IWM, KRE, ^GSPC (via SPY proxy)
- Smart caching: Only fetches if data through yesterday's close doesn't exist

**Fallback: Yahoo Finance**
- Used for: ^VIX (not available in Alpha Vantage free tier)
- Fallback: If Alpha Vantage fails or budget exhausted
- Cached with 24-hour TTL

### New Components

1. **AlphaVantageClient** (`backend/analytics/data_fetchers/alphavantage_client.py`)
   - Handles Alpha Vantage API calls
   - Smart daily caching logic
   - API budget tracking (25 calls/day)
   - Rate limiting (12 seconds between requests)

2. **MarketDataManager** (`backend/analytics/data_fetchers/market_data_manager.py`)
   - Unified interface for market data fetching
   - Routes requests intelligently:
     - ^VIX → Always Yahoo Finance
     - Others → Alpha Vantage (with Yahoo fallback)
   - Checks cache before fetching

3. **API Budget Tracker** (`backend/analytics/utils/api_budget_tracker.py`)
   - Tracks daily API call usage
   - Exposed via `/api/budget` endpoint

## Key Features

### Smart Daily Caching

The system checks if data through **yesterday's close** exists before fetching:
- If cached data includes yesterday → Use cache (0 API calls)
- If data is stale/missing → Fetch from Alpha Vantage
- Perfect for weekly usage patterns

### API Budget Management

- Automatically tracks daily API usage
- Falls back to Yahoo Finance if budget exhausted
- Budget resets at midnight UTC
- Monitor via `/api/budget` endpoint

### Symbol Mapping

- `^GSPC` → Uses SPY as proxy (Alpha Vantage free tier doesn't support indices)
- `^VIX` → Always uses Yahoo Finance (not available in Alpha Vantage)
- Other tickers → Direct mapping (SPY, QQQ, RSP, IWM, KRE)

## Setup Requirements

### Environment Variables

Add to `backend/.env`:
```
ALPHA_VANTAGE_API_KEY=your_api_key_here
FRED_API_KEY=your_fred_api_key_here
```

Get Alpha Vantage API key: https://www.alphavantage.co/support/#api-key

### Dependencies

Added to `requirements.txt`:
```
alpha-vantage>=2.3.1
```

Install:
```bash
pip install -r requirements.txt
```

## API Usage

### Typical Daily Usage

With 6 tickers on Alpha Vantage:
- **First run**: ~6-7 API calls (fetching current data)
- **Same day, second run**: 0 API calls (uses cache)
- **Weekly usage**: ~6-7 calls to catch up on missing days
- **Well under 25 calls/day limit**

### Budget Monitoring

Check API usage:
```bash
curl http://localhost:8000/api/budget
```

Response:
```json
{
  "used": 7,
  "limit": 25,
  "remaining": 18,
  "resets_at": "2025-12-20T00:00:00Z",
  "date": "2025-12-19"
}
```

## Files Modified

### New Files
- `backend/analytics/data_fetchers/alphavantage_client.py`
- `backend/analytics/data_fetchers/market_data_manager.py`
- `backend/analytics/utils/api_budget_tracker.py`
- `backend/analytics/utils/__init__.py`

### Updated Files
- `backend/requirements.txt` - Added alpha-vantage
- `backend/analytics/core/frs_calculator.py` - Uses MarketDataManager
- `backend/analytics/core/volatility_predictor.py` - Uses MarketDataManager
- `backend/analytics/core/categories/base_category.py` - Supports market_data parameter
- `backend/analytics/core/categories/valuation.py` - Uses market_data
- `backend/analytics/core/categories/leverage_stability.py` - Uses market_data
- `backend/analytics/core/categories/sentiment.py` - Uses market_data
- `backend/analytics/core/categories/earnings_margins.py` - Uses market_data
- `backend/api/main.py` - Added `/api/budget` endpoint

## Testing

### Test Alpha Vantage Client
```bash
cd backend
python -c "from analytics.data_fetchers.alphavantage_client import AlphaVantageClient; client = AlphaVantageClient(); data = client.fetch_ticker('SPY', period='1y'); print(f'Success! Fetched {len(data)} data points')"
```

### Test Market Data Manager
```bash
cd backend
python -c "from analytics.data_fetchers.market_data_manager import MarketDataManager; mgr = MarketDataManager(); data = mgr.fetch_ticker('SPY', period='1y'); print(f'Success! Fetched {len(data)} data points')"
```

### Test Full System
```bash
# Start server
cd backend
python -m uvicorn api.main:app --reload

# Test endpoints
curl http://localhost:8000/api/frs
curl http://localhost:8000/api/volatility
curl http://localhost:8000/api/cmds
curl http://localhost:8000/api/budget
```

## Troubleshooting

### "No time series data in response"
- **Cause**: Using premium endpoint or API key not set
- **Solution**: Verify API key in `.env` file, ensure using free tier endpoint

### "API budget exhausted"
- **Cause**: Exceeded 25 calls/day limit
- **Solution**: System automatically falls back to Yahoo Finance, wait for reset

### "^GSPC not found"
- **Cause**: Alpha Vantage free tier doesn't support indices
- **Solution**: System automatically uses SPY as proxy (they track closely)

### Yahoo Finance fallback still failing
- **Cause**: IP rate-limited or API changes
- **Solution**: System uses stale cache with warning, wait for rate limit to clear

## Benefits

1. **More Reliable**: Alpha Vantage is more stable than Yahoo Finance scraping
2. **Better Caching**: Smart daily caching reduces unnecessary API calls
3. **Budget Aware**: Automatic tracking prevents exceeding limits
4. **Weekly Friendly**: Perfect for intermittent use - only fetches what's missing
5. **Automatic Fallback**: Falls back to Yahoo Finance if Alpha Vantage fails

## Migration Notes

- **Backward Compatible**: Old code using `yfinance_client` still works (via MarketDataManager)
- **No Data Loss**: All cached Yahoo Finance data is preserved
- **Gradual Migration**: System can use both sources during transition

## Future Improvements

- Consider premium Alpha Vantage tier for more features (adjusted data, indices)
- Add more data sources as fallbacks
- Implement historical data backfill optimization
- Add data quality monitoring

## Summary

✅ **Alpha Vantage Integration**: Complete
✅ **Smart Caching**: Implemented
✅ **Budget Tracking**: Active
✅ **Fallback System**: Working
✅ **Documentation**: Updated

The system now provides more reliable market data access while efficiently managing API usage within free tier limits.


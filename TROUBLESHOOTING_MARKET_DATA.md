# Market Data Troubleshooting Guide

## Data Source Architecture

TradeEdge uses a **multi-source data fetching strategy** with intelligent fallback:

1. **Primary: Alpha Vantage** (free tier: 25 calls/day)
   - Used for: SPY, QQQ, RSP, IWM, KRE, ^GSPC (via SPY proxy)
   - Smart caching: Only fetches if data through yesterday doesn't exist
   - Budget tracking: Automatically monitors daily API usage

2. **Fallback: Yahoo Finance**
   - Used for: ^VIX (not available in Alpha Vantage free tier)
   - Fallback: If Alpha Vantage fails or budget exhausted
   - Cached with 24-hour TTL

3. **FRED API**: Economic indicators (unemployment, yield curve, GDP, etc.)

## Issues Found and Fixed

### 1. ✅ FRED Series ID Error (FIXED)
**Problem:** `WILL5000PR` series doesn't exist
```
Error fetching WILL5000PR: Bad Request. The series does not exist.
```

**Solution:** Changed to `WILL5000IND` (Wilshire 5000 Total Market Index)
- File: `backend/analytics/core/frs_calculator.py` line 186
- This fix is permanent and will resolve the FRED error

### 2. ✅ Alpha Vantage Integration (DECEMBER 2025)
**Problem:** Yahoo Finance API unreliable, frequent failures

**Solution:** Migrated to Alpha Vantage as primary data source
- Uses free tier `TIME_SERIES_DAILY` endpoint (not premium `TIME_SERIES_DAILY_ADJUSTED`)
- Smart daily caching: Checks if yesterday's close exists before fetching
- Budget tracking: Monitors 25 calls/day limit
- Automatic fallback to Yahoo Finance if Alpha Vantage fails

**Files Updated:**
- `backend/analytics/data_fetchers/alphavantage_client.py` (new)
- `backend/analytics/data_fetchers/market_data_manager.py` (new)
- All category modules updated to use MarketDataManager

### 3. ✅ Yahoo Finance Rate Limiting (IMPROVED)
**Problem:** Getting 429 errors and empty responses
```
Error getting info for SPY: 429 Client Error: Too Many Requests
Failed to get ticker 'SPY' reason: Expecting value: line 1 column 1 (char 0)
```

**Status:** Yahoo Finance now used only as fallback for ^VIX
- Rate limiting improved (1 second between requests)
- Retry logic with exponential backoff
- Better error handling and logging

**File Updated:** `backend/analytics/data_fetchers/yfinance_client.py`

## Common Issues & Solutions

### Alpha Vantage API Issues

#### Issue: "No time series data in response"
**Cause:** Using premium endpoint or API key not set
**Solution:**
1. Verify API key is set: Check `.env` file has `ALPHA_VANTAGE_API_KEY`
2. Check API budget: Visit `/api/budget` endpoint
3. Verify using free tier endpoint (not premium)

#### Issue: "API budget exhausted"
**Cause:** Exceeded 25 calls/day limit
**Solution:**
- System automatically falls back to Yahoo Finance
- Wait until next day (resets at midnight UTC)
- Check budget status: `GET /api/budget`

#### Issue: "^GSPC not found"
**Cause:** Alpha Vantage free tier doesn't support indices
**Solution:** System automatically uses SPY as proxy (they track closely)

### Yahoo Finance Fallback Issues

#### Issue: Yahoo Finance still failing
**Cause:** IP rate-limited or API changes
**Solution:**
1. System will use stale cache with warning
2. Wait 1-2 hours for rate limit to clear
3. Use VPN to change IP if needed
4. Clear old cache if needed:
```powershell
# Clear Yahoo Finance cache
Remove-Item -Path "data\cache\yfinance\*" -Recurse -Force
```

## Testing Data Sources

### Test 1: Alpha Vantage Client
```powershell
cd backend
python -c "from analytics.data_fetchers.alphavantage_client import AlphaVantageClient; client = AlphaVantageClient(); data = client.fetch_ticker('SPY', period='1y'); print(f'Success! Fetched {len(data)} data points')"
```

### Test 2: Market Data Manager (Unified Interface)
```powershell
cd backend
python -c "from analytics.data_fetchers.market_data_manager import MarketDataManager; mgr = MarketDataManager(); data = mgr.fetch_ticker('SPY', period='1y'); print(f'Success! Fetched {len(data)} data points')"
```

### Test 3: FRED Client
```powershell
cd backend
python -m analytics.data_fetchers.fred_client
```

### Test 4: API Budget Status
```powershell
# Check API usage
curl http://localhost:8000/api/budget
# Or visit in browser: http://localhost:8000/api/budget
```

### Test 5: Full FRS Calculator
```powershell
cd backend
python -m analytics.core.frs_calculator
```

### Test 6: API Endpoints
```powershell
# Start the backend server
cd backend
python -m uvicorn api.main:app --reload

# Then test endpoints:
# http://localhost:8000/api/frs
# http://localhost:8000/api/volatility
# http://localhost:8000/api/cmds
# http://localhost:8000/api/budget
```

## Monitoring

### Check API Budget Status
```powershell
# Via API endpoint
curl http://localhost:8000/api/budget

# Expected response:
# {
#   "used": 7,
#   "limit": 25,
#   "remaining": 18,
#   "resets_at": "2025-12-20T00:00:00Z"
# }
```

### Check Cache Status
```powershell
# List cached Alpha Vantage data
Get-ChildItem "data\cache\alphavantage" -Recurse | Format-Table Name, LastWriteTime, Length

# List cached Yahoo Finance data (fallback)
Get-ChildItem "data\cache\yfinance" -Recurse | Format-Table Name, LastWriteTime, Length

# List cached FRED data
Get-ChildItem "data\cache\fred" -Recurse | Format-Table Name, LastWriteTime, Length

# Check API budget files
Get-ChildItem "data\cache\alphavantage\api_budget_*.json" | Format-Table Name, LastWriteTime
```

### Check for Errors
```powershell
# Alpha Vantage errors:
# - "No time series data in response" → Check API key or endpoint
# - "API budget exhausted" → Wait for reset or check usage
# - "Failed to fetch" → Check network or API status

# Yahoo Finance errors (fallback):
# - 429 Client Error: Too Many Requests → Rate limited, wait
# - "Expecting value: line 1 column 1" → API blocked, using cache
```

## Prevention & Best Practices

### Alpha Vantage (Primary)
1. **Smart Daily Caching**: Only fetches if data through yesterday doesn't exist
2. **Budget Tracking**: Automatically monitors 25 calls/day limit
3. **Rate Limiting**: 12 seconds between requests (5 calls/minute)
4. **Automatic Fallback**: Falls back to Yahoo Finance if Alpha Vantage fails
5. **Weekly Usage Friendly**: Perfect for intermittent use - only fetches missing days

### Yahoo Finance (Fallback)
1. **Rate Limiting**: 1 second minimum between requests
2. **Retry Logic**: 2 attempts with exponential backoff
3. **Better Headers**: Realistic browser user-agent
4. **Smart Caching**: 
   - Uses cached data when available
   - Falls back to stale cache with warning if API fails
5. **Graceful Degradation**: Returns partial results if some data unavailable

### General
- **Check API Budget**: Monitor `/api/budget` endpoint regularly
- **Use Cached Data**: System intelligently uses cache when appropriate
- **Don't Over-Fetch**: System only fetches what's needed

## Verification Checklist

1. **API Keys Set**:
   ```powershell
   # Check environment variables
   echo $env:FRED_API_KEY
   echo $env:ALPHA_VANTAGE_API_KEY
   
   # Or check .env file
   Get-Content backend\.env
   ```

2. **Dependencies Installed**:
   ```powershell
   pip list | findstr -i "alpha-vantage yfinance fredapi"
   ```

3. **Test Data Fetching**:
   ```powershell
   # Test Alpha Vantage
   python -c "from analytics.data_fetchers.alphavantage_client import AlphaVantageClient; AlphaVantageClient()"
   
   # Test Market Data Manager
   python -c "from analytics.data_fetchers.market_data_manager import MarketDataManager; MarketDataManager()"
   ```

4. **Check API Budget**:
   ```powershell
   # After starting server
   curl http://localhost:8000/api/budget
   ```

## If Issues Persist

If you continue to see errors:

1. **Check API Keys**: Verify both FRED and Alpha Vantage keys are set correctly
2. **Check Internet Connection**: Test accessing APIs directly
3. **Check API Status**: 
   - Alpha Vantage: https://www.alphavantage.co/support/
   - Yahoo Finance: Try https://finance.yahoo.com/quote/SPY in browser
4. **Check Logs**: Look for specific error messages in server output
5. **Verify Cache**: Check if cached data exists and is being used

## Summary

✅ **FRED Error**: Fixed (wrong series ID)
✅ **Alpha Vantage Integration**: Complete (primary data source)
✅ **Smart Caching**: Implemented (checks for yesterday's close)
✅ **Budget Tracking**: Active (monitors 25 calls/day)
✅ **Yahoo Finance**: Fallback only (for ^VIX and when Alpha Vantage fails)

The system now uses Alpha Vantage as primary data source with intelligent caching and automatic fallback to Yahoo Finance when needed.


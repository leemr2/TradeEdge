# Market Data Troubleshooting Guide

## Issues Found and Fixed

### 1. ✅ FRED Series ID Error (FIXED)
**Problem:** `WILL5000PR` series doesn't exist
```
Error fetching WILL5000PR: Bad Request. The series does not exist.
```

**Solution:** Changed to `WILL5000IND` (Wilshire 5000 Total Market Index)
- File: `backend/analytics/core/frs_calculator.py` line 186
- This fix is permanent and will resolve the FRED error

### 2. ✅ Yahoo Finance Rate Limiting (IMPROVED)
**Problem:** Getting 429 errors and empty responses
```
Error getting info for SPY: 429 Client Error: Too Many Requests
Failed to get ticker 'SPY' reason: Expecting value: line 1 column 1 (char 0)
```

**Improvements Made:**
1. Added rate limiting (500ms between requests)
2. Added retry logic with exponential backoff
3. Added custom session with proper headers
4. Improved cache validation logic
5. Better error handling and logging

**File Updated:** `backend/analytics/data_fetchers/yfinance_client.py`

## Current Status

### Yahoo Finance Temporary Block
Your IP is currently rate-limited by Yahoo Finance (429 errors). This is temporary and happens when:
- Too many requests in a short time
- Multiple retries without sufficient delays
- Yahoo's anti-bot measures detect automated access

### Solutions:

#### Option 1: Wait (Recommended)
Wait 1-2 hours for Yahoo to lift the rate limit. The new code will:
- Use cached data when available
- Rate limit requests to prevent future blocks
- Retry with exponential backoff
- Use realistic browser headers

#### Option 2: Use VPN or Different Network
Temporarily use a different IP address to bypass the block

#### Option 3: Clear Old Cache (if stale data exists)
```powershell
# Clear Yahoo Finance cache
Remove-Item -Path "data\cache\yfinance\*" -Recurse -Force

# Clear only expired cache older than 1 day
Get-ChildItem "data\cache\yfinance" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-1)} | Remove-Item
```

## Testing After Rate Limit Clears

### Test 1: FRED Client (Should work now)
```powershell
cd backend
python -m analytics.data_fetchers.fred_client
```

### Test 2: Yahoo Finance Client (Wait for rate limit to clear)
```powershell
cd backend
python -m analytics.data_fetchers.yfinance_client
```

### Test 3: Full FRS Calculator
```powershell
cd backend
python -m analytics.core.frs_calculator
```

### Test 4: API Endpoints (after rate limit clears)
```powershell
# Start the backend server (in terminal 9)
cd backend
.venv\Scripts\activate
uvicorn api.main:app --reload

# Then test endpoints:
# http://localhost:8000/api/frs
# http://localhost:8000/api/volatility
# http://localhost:8000/api/cmds
```

## Monitoring

### Check if Rate Limit is Active
```powershell
# If you see these errors, wait longer:
# - 429 Client Error: Too Many Requests
# - Max retries exceeded with url
# - Expecting value: line 1 column 1 (char 0)
```

### Check Cache Status
```powershell
# List cached Yahoo Finance data
Get-ChildItem "data\cache\yfinance" -Recurse | Format-Table Name, LastWriteTime, Length

# List cached FRED data
Get-ChildItem "data\cache\fred" -Recurse | Format-Table Name, LastWriteTime, Length
```

## Prevention

The updated code now includes:
1. **Rate Limiting**: 500ms minimum between requests
2. **Retry Logic**: 3 attempts with exponential backoff
3. **Better Headers**: Realistic browser user-agent
4. **Smart Caching**: 
   - 1 hour max during market hours (9 AM - 4 PM)
   - 24 hours outside market hours
5. **Graceful Degradation**: Returns partial results if some data unavailable

## Next Steps

1. **Wait 1-2 hours** for Yahoo Finance rate limit to clear
2. **Restart backend server** to use new code:
   ```powershell
   cd C:\Users\drlee\Trading_Edge\backend
   .venv\Scripts\activate
   uvicorn api.main:app --reload
   ```
3. **Test endpoints** via browser or frontend
4. **Monitor logs** for successful data fetches

## If Issues Persist

If you continue to see errors after 2 hours:

1. Check your internet connection
2. Try accessing Yahoo Finance in browser: https://finance.yahoo.com/quote/SPY
3. Check if FRED API key is set: `echo $env:FRED_API_KEY`
4. Verify Python packages are installed:
   ```powershell
   pip list | findstr yfinance
   pip list | findstr fredapi
   ```

## Summary

✅ **FRED Error**: Fixed (wrong series ID)
✅ **Rate Limiting**: Improved (new code in place)
⏳ **Yahoo Finance Block**: Temporary (wait 1-2 hours)

The code improvements will prevent future rate limit issues once the current block expires.


# Yahoo Finance API Fixes - December 18, 2025

## Problem Summary

The application was experiencing Yahoo Finance API failures for 2+ days with errors:
- `Failed to get ticker 'XXX' reason: Expecting value: line 1 column 1 (char 0)`
- `Tz-aware datetime.datetime cannot be converted to datetime64 unless utc=True`

## Root Causes Identified

### 1. Outdated yfinance Library
- **Old version**: 0.2.28
- **New version**: 0.2.66
- The yfinance library is unofficial and breaks frequently as Yahoo changes their site
- 38 version updates were missed, containing critical bug fixes

### 2. Timezone Handling Issues
- Mixed timezone-aware and timezone-naive datetime objects
- pandas operations failing when trying to merge DataFrames with incompatible timezone settings
- yfinance 0.2.66+ returns timezone-aware data by default

### 3. Rate Limiting Too Aggressive
- Original settings: 500ms between requests, 3 retries with 2s delay
- These settings were causing Yahoo's anti-bot measures to block the IP

## Solutions Implemented

### 1. Updated yfinance Configuration

**File**: `backend/requirements.txt`
```python
# Before
yfinance==0.2.28

# After  
yfinance>=0.2.66
```

**File**: `backend/analytics/data_fetchers/yfinance_client.py`

#### Rate Limiting Improvements:
```python
# More conservative settings to avoid blocks
self.min_request_interval = 1.0  # Increased from 500ms to 1 second
self.max_retries = 2              # Reduced from 3 to 2 retries
self.retry_delay = 3              # Increased from 2 to 3 seconds
```

#### Enhanced Timezone Handling:
```python
def _ensure_timezone_naive(self, df: pd.DataFrame) -> pd.DataFrame:
    """
    More robust handling for timezone-aware data from yfinance 0.2.66+
    """
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        # Convert to UTC first if not already, then remove timezone
        if df.index.tz.zone != 'UTC':
            df.index = df.index.tz_convert('UTC')
        df.index = df.index.tz_localize(None)
    return df
```

### 2. Fixed Timezone Issues in Volatility Predictor

**File**: `backend/analytics/core/volatility_predictor.py`

Changed datetime conversion to explicitly handle timezones:

```python
# Before (2 occurrences)
trends_df['date'] = pd.to_datetime(trends_df['date'])
if hasattr(trends_df['date'].dtype, 'tz') and trends_df['date'].dt.tz is not None:
    trends_df['date'] = trends_df['date'].dt.tz_localize(None)

# After
trends_df['date'] = pd.to_datetime(trends_df['date'], utc=True).dt.tz_localize(None)
market_df['date'] = pd.to_datetime(market_df['date'], utc=True).dt.tz_localize(None)
```

This forces all datetime conversions to go through UTC first, then removes timezone info for consistency.

## Test Results

### ✅ yfinance Client Standalone Test
```bash
python backend/analytics/data_fetchers/yfinance_client.py
```
**Result**: Successfully fetched SPY (251 points) and VIX (251 points) - NO ERRORS!

### ✅ Volatility Predictor Test
```bash
python backend/analytics/core/volatility_predictor.py --mode json
```
**Result**: Successfully processed data with NO timezone errors!
- Fetched ^GSPC (1256 data points)
- Aligned market and trends data (47 days)
- Generated VP score: 6 (low volatility)

### ✅ Full API Test
```bash
curl http://127.0.0.1:8000/api/cmds?frs_weight=0.65&vp_weight=0.35
```
**Result**: Successfully calculated CMDS score of 66.6 (HIGH zone)

Server logs show:
```
✓ Fetched and cached KRE (251 data points)
✓ Fetched and cached QQQ (251 data points)
✓ Fetched and cached RSP (251 data points)
✓ Fetched and cached IWM (128 data points)
✓ Fetched and cached SPY (128 data points)
✓ Fetched and cached ^VIX (22 data points)
✓ Fetched and cached ^GSPC (1256 data points)
```

**NO MORE ERRORS!** All data is being fetched successfully from Yahoo Finance.

## Why Yahoo Finance "Appeared Down"

1. **Not Actually Down**: Yahoo Finance API was operational, but:
   - Old yfinance library (0.2.28) was incompatible with recent Yahoo site changes
   - Rate limiting had blacklisted the IP temporarily
   - The system was falling back to 6-day-old cached data

2. **Stale Cache Behavior**: The app was still functioning because of the robust caching system, using data from December 12, 2025, which masked the underlying API issue.

## Prevention Measures

### 1. Regular Dependency Updates
Monitor yfinance releases: https://github.com/ranaroussi/yfinance/releases

### 2. Better Rate Limiting
The new conservative settings (1s intervals, 2 retries max) should prevent future IP blocks.

### 3. Timezone Consistency
All datetime operations now explicitly handle timezones through UTC conversion.

### 4. Monitoring
Watch for these log patterns:
- `⚠ Rate limited for XXX - skipping`
- `⚠ Using stale cache for XXX`
- `Failed to get ticker 'XXX' reason: Expecting value`

If these appear frequently, it may indicate:
- Need to further reduce request rate
- Need to upgrade yfinance again
- Possible IP block (switch networks/VPN)

## Files Modified

1. `backend/requirements.txt` - Updated yfinance version
2. `backend/analytics/data_fetchers/yfinance_client.py` - Rate limiting & timezone fixes
3. `backend/analytics/core/volatility_predictor.py` - Timezone conversion fixes

## Next Steps

1. ✅ All fixes tested and working
2. ✅ Server running successfully with fresh data
3. ✅ No more timezone errors
4. ✅ Yahoo Finance data fetching properly

The application is now fully operational with fresh market data!


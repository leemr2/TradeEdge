"""
Quick Start: Google Trends Market Predictor
============================================
Simplified demo to see the concept in action immediately
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("""
╔══════════════════════════════════════════════════════════════╗
║  QUICK DEMO: Google Trends → Market Volatility Prediction   ║
╚══════════════════════════════════════════════════════════════╝

This demo shows how search interest correlates with market volatility.
""")

# Check dependencies
try:
    from pytrends.request import TrendReq
    import yfinance as yf
    print("✓ All packages installed\n")
except ImportError as e:
    print(f"❌ Missing package: {e}")
    print("\nInstall with:")
    print("pip install pytrends yfinance --break-system-packages\n")
    exit(1)

# Configuration
KEYWORDS = ['stock market crash', 'recession', 'market volatility']
TIMEFRAME = 'today 12-m'  # Last 12 months

print("="*60)
print("STEP 1: Fetching Google Trends Data")
print("="*60)
print(f"Keywords: {KEYWORDS}")
print(f"Timeframe: {TIMEFRAME}\n")

# Initialize Google Trends
pytrends = TrendReq(hl='en-US', tz=360)

# Fetch trends
try:
    pytrends.build_payload(KEYWORDS, timeframe=TIMEFRAME)
    trends = pytrends.interest_over_time()
    
    if not trends.empty:
        trends = trends.drop('isPartial', axis=1, errors='ignore')
        print(f"✓ Got {len(trends)} days of search data")
        print(f"  Trends date range: {trends.index.min()} to {trends.index.max()}\n")
    else:
        print("❌ No trend data returned")
        exit(1)
        
except Exception as e:
    print(f"❌ Error fetching trends: {e}")
    exit(1)

print("="*60)
print("STEP 2: Fetching Market Data (VIX)")
print("="*60)

# Fetch VIX (volatility index)
try:
    vix_data = yf.download('^VIX', period='1y', progress=False)
    vix = vix_data['Close']
    print(f"✓ Got {len(vix)} days of VIX data")
    
    # Ensure vix index is timezone-naive to match trends data
    if hasattr(vix.index, 'tz') and vix.index.tz is not None:
        vix.index = vix.index.tz_localize(None)
    print(f"  VIX date range: {vix.index.min()} to {vix.index.max()}\n")
    
except Exception as e:
    print(f"❌ Error fetching VIX: {e}")
    exit(1)

print("="*60)
print("STEP 3: Analyzing Correlation")
print("="*60)

# Normalize both indices to just dates (no time components)
trends.index = pd.to_datetime(trends.index).normalize()
vix.index = pd.to_datetime(vix.index).normalize()

# Check if trends is weekly data (common for 12-month timeframe)
trends_freq = pd.infer_freq(trends.index)
print(f"\nDetected frequency - Trends: {trends_freq or 'irregular'}, VIX: daily")

# If trends is weekly, resample VIX to weekly to match
if trends_freq in ['W', 'W-SUN', 'W-MON'] or (len(trends) < 100 and len(vix) > 200):
    print("✓ Resampling VIX to weekly frequency to match Trends data...")
    
    # Resample VIX to weekly, taking the mean for each week
    vix_weekly = vix.resample('W-SUN').mean()
    
    # Align to trends dates using merge_asof (nearest date matching)
    trends_df = trends.reset_index()
    vix_df = vix_weekly.reset_index()
    trends_df.columns = ['date'] + list(trends.columns)
    vix_df.columns = ['date', 'VIX']
    
    # Sort both by date
    trends_df = trends_df.sort_values('date')
    vix_df = vix_df.sort_values('date')
    
    # Merge with tolerance of 3 days
    merged = pd.merge_asof(trends_df, vix_df, on='date', direction='nearest', tolerance=pd.Timedelta('3d'))
    
    # Drop rows where VIX is NaN (no match found)
    merged = merged.dropna(subset=['VIX'])
    
    if len(merged) == 0:
        print("❌ Error: Could not align trends and VIX data")
        exit(1)
    
    print(f"✓ Successfully aligned {len(merged)} data points\n")
    merged = merged.set_index('date')
    trends_aligned = merged[KEYWORDS]
    vix_aligned = merged['VIX']
else:
    # Daily data - direct intersection
    common_dates = trends.index.intersection(vix.index)
    
    if len(common_dates) == 0:
        print("❌ Error: No overlapping dates found")
        exit(1)
    
    trends_aligned = trends.loc[common_dates]
    vix_aligned = vix.loc[common_dates]
    print(f"✓ Found {len(common_dates)} overlapping dates\n")

# Calculate correlations
print("\nCorrelation with VIX (higher = stronger relationship):")
print("-" * 60)

for keyword in KEYWORDS:
    correlation = trends_aligned[keyword].corr(vix_aligned)
    print(f"  {keyword:30s}: {correlation:+.3f}")

# Composite fear index
composite_fear = trends_aligned[KEYWORDS].mean(axis=1)

if len(composite_fear) == 0:
    print("❌ Error: No data to analyze after alignment")
    exit(1)

composite_corr = composite_fear.corr(vix_aligned)

print(f"\n  {'Composite Fear Index':30s}: {composite_corr:+.3f}")

print("\n" + "="*60)
print("STEP 4: Current Market Assessment")
print("="*60)

# Get recent data
recent_days = 7
recent_trends = trends_aligned.tail(recent_days)
recent_vix = vix_aligned.tail(recent_days)

# Calculate statistics
current_fear = composite_fear.iloc[-1]
avg_fear = composite_fear.mean()
current_vix = recent_vix.iloc[-1]
avg_vix = vix_aligned.mean()

# Calculate volatility of search (erratic movement indicator)
search_volatility = composite_fear.tail(30).std()
avg_search_volatility = composite_fear.std()

print(f"\nCurrent State (as of {trends.index[-1].strftime('%Y-%m-%d')}):")
print("-" * 60)
print(f"  Current VIX:              {current_vix:6.2f}")
print(f"  Historical Avg VIX:       {avg_vix:6.2f}")
print(f"  VIX Status:               {current_vix - avg_vix:+6.2f} from average")

print(f"\n  Current Fear Index:       {current_fear:6.2f}")
print(f"  Historical Avg Fear:      {avg_fear:6.2f}")
print(f"  Fear Status:              {current_fear - avg_fear:+6.2f} from average")

print(f"\n  Search Volatility (30d):  {search_volatility:6.2f}")
print(f"  Avg Search Volatility:    {avg_search_volatility:6.2f}")
print(f"  Volatility Status:        {search_volatility - avg_search_volatility:+6.2f} from average")

# Simple risk assessment
risk_score = 0

if current_vix > avg_vix + 5:
    risk_score += 30
elif current_vix > avg_vix:
    risk_score += 15

if current_fear > avg_fear + 10:
    risk_score += 30
elif current_fear > avg_fear:
    risk_score += 15

if search_volatility > avg_search_volatility * 1.5:
    risk_score += 40
elif search_volatility > avg_search_volatility:
    risk_score += 20

print("\n" + "="*60)
print("RISK ASSESSMENT")
print("="*60)
print(f"\nSimple Risk Score: {risk_score}/100")

if risk_score >= 70:
    print("⚠️  HIGH RISK - Markets showing elevated volatility signals")
    print("   Consider: Reducing positions, buying protection")
elif risk_score >= 40:
    print("⚡ MODERATE RISK - Some volatility indicators elevated")
    print("   Consider: Defensive positioning, monitoring closely")
else:
    print("✓ LOW RISK - Market sentiment appears relatively calm")
    print("   Consider: Normal positioning")

print("\n" + "="*60)
print("RECENT TREND (Last 7 days)")
print("="*60)

print("\nDate          Fear Index    VIX")
print("-" * 40)
for date in recent_trends.index:
    fear = composite_fear.loc[date]
    vix_val = vix_aligned.loc[date]
    print(f"{date.strftime('%Y-%m-%d')}      {fear:5.1f}      {vix_val:6.2f}")

print("\n" + "="*60)
print("KEY INSIGHTS")
print("="*60)

print(f"""
1. CORRELATION: The composite fear index has a correlation of {composite_corr:.3f}
   with the VIX. Positive correlation means they move together.

2. CURRENT STATE: Your risk score is {risk_score}/100, indicating
   {"high" if risk_score >= 70 else "moderate" if risk_score >= 40 else "low"} 
   volatility risk based on search patterns.

3. PATTERN: {"Search volatility is elevated - erratic search behavior detected!" 
             if search_volatility > avg_search_volatility * 1.5 
             else "Search patterns are relatively stable."}

4. ACTIONABLE: This is a SENTIMENT indicator, not a price predictor.
   Use it to gauge market nervousness, not to time exact trades.
""")

print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)
print("""
1. Run this daily to track changes in risk levels
2. Watch for SPIKES in search volatility (most predictive)
3. Compare against actual VIX movements over time
4. When risk is high, consider portfolio hedges
5. See GUIDE.md for the full methodology
6. Try volatility_predictor.py for machine learning approach
""")

print("\n✓ Demo complete!\n")

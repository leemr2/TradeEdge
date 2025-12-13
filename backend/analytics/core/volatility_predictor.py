"""
Volatility Spike Predictor V2
Refactored for TradeEdge: JSON output, model caching, CLI modes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import pickle
import warnings
warnings.filterwarnings('ignore')

try:
    from pytrends.request import TrendReq
    import yfinance as yf
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
except ImportError as e:
    print(f"Missing package: {e}")
    exit(1)

# Import our fixed YFinanceClient
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_fetchers.yfinance_client import YFinanceClient


class VolatilityPredictorV2:
    """
    Version 2: Focuses on REGIME CHANGES rather than absolute volatility levels
    Key improvements:
    - Detects transitions from calm to volatile
    - Uses rate of change in features
    - Filters out persistent states
    - Better threshold calibration
    """
    
    def __init__(self, model_dir: str = "data/cache/models"):
        """Initialize with improved keyword selection"""
        
        # Refined keywords - remove terms that cause false positives
        self.fear_keywords = [
            'stock market crash',
            'recession',
            'financial crisis',
            'market crash'
        ]
        
        # Add keywords that spike during TRANSITIONS
        self.transition_keywords = [
            'buy puts',
            'market correction',
            'volatility index',
            'sell stocks'
        ]
        
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize YFinanceClient for reliable data fetching
        self.yfinance = YFinanceClient()
        
        # Storage
        self.trends_data = None
        self.market_data = None
        self.features = None
        self.labels = None
        self.model = None
        self.scaler = None
        
    def fetch_google_trends(self, keywords, timeframe='today 5-y', cache_path=None, ttl_hours=24):
        """Fetch Google Trends data with caching and rate limiting"""
        print(f"Fetching Google Trends data for {len(keywords)} keywords...")
        
        # Check cache first
        if cache_path:
            cache_file = Path(cache_path)
            if cache_file.exists():
                try:
                    file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    age = datetime.now() - file_time
                    if age.total_seconds() / 3600 < ttl_hours:
                        print(f"  ✓ Using cached Google Trends data")
                        return pd.read_pickle(cache_file)
                except Exception as e:
                    print(f"  ⚠ Cache read error: {e}")
        
        all_trends = pd.DataFrame()
        import time
        
        for i in range(0, len(keywords), 5):
            batch = keywords[i:i+5]
            
            # Add delay between requests to avoid rate limiting
            if i > 0:
                delay = 5  # 5 seconds between batches
                print(f"  ⏳ Waiting {delay}s to avoid rate limits...")
                time.sleep(delay)
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.pytrends.build_payload(batch, timeframe=timeframe)
                    trends = self.pytrends.interest_over_time()
                    
                    if not trends.empty:
                        trends = trends.drop('isPartial', axis=1, errors='ignore')
                        
                        if all_trends.empty:
                            all_trends = trends
                        else:
                            all_trends = all_trends.join(trends, how='outer')
                            
                    print(f"  ✓ Fetched batch {i//5 + 1}")
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 10  # Exponential backoff: 10s, 20s, 30s
                            print(f"  ⚠ Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                            time.sleep(wait_time)
                        else:
                            print(f"  ✗ Error after {max_retries} attempts: {e}")
                    else:
                        print(f"  ✗ Error: {e}")
                        break  # Non-rate-limit error, don't retry
        
        # Save to cache
        if cache_path and not all_trends.empty:
            try:
                cache_file = Path(cache_path)
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                all_trends.to_pickle(cache_file)
                print(f"  ✓ Cached Google Trends data")
            except Exception as e:
                print(f"  ⚠ Could not cache data: {e}")
        
        return all_trends
    
    def fetch_market_data(self, ticker='^GSPC', vix_ticker='^VIX', period='5y'):
        """Fetch market data using YFinanceClient with proper error handling"""
        print(f"\nFetching market data...")
        
        try:
            # Use our fixed YFinanceClient instead of direct yf.download
            market = self.yfinance.fetch_ticker(ticker, period=period, ttl_hours=24)
            vix = self.yfinance.fetch_ticker(vix_ticker, period=period, ttl_hours=24)
            
            if market.empty or vix.empty:
                raise ValueError(f"No data returned for {ticker} or {vix_ticker}")
            
            market_data = pd.DataFrame()
            market_data['close'] = market['Close']
            market_data['volume'] = market['Volume']
            market_data['vix'] = vix['Close']
            market_data['returns'] = market_data['close'].pct_change()
            market_data['realized_vol'] = market_data['returns'].rolling(20).std() * np.sqrt(252)
            
            # Remove timezone info from index to avoid issues
            if hasattr(market_data.index, 'tz') and market_data.index.tz is not None:
                market_data.index = market_data.index.tz_localize(None)
            
            print(f"  ✓ Fetched {len(market_data)} days")
            
            return market_data
            
        except Exception as e:
            print(f"  ✗ Error fetching market data: {e}")
            raise
    
    def create_change_focused_features(self, trends_data, market_data=None):
        """
        KEY IMPROVEMENT: Focus on CHANGES and ACCELERATION
        Fallback: Use market-only features if trends_data is None
        """
        print("\nCreating CHANGE-FOCUSED features...")
        
        # If no trends data, use market-based features only
        if trends_data is None or trends_data.empty:
            if market_data is None:
                raise ValueError("Need either trends_data or market_data")
            
            print("  Using market-only features (Google Trends unavailable)")
            features = pd.DataFrame(index=market_data.index)
            
            # Market volatility features
            features['vix_level'] = market_data['vix']
            features['vix_roc_5d'] = market_data['vix'].pct_change(5)
            features['vix_roc_10d'] = market_data['vix'].pct_change(10)
            features['vix_acceleration'] = features['vix_roc_5d'].diff(5)
            features['vix_zscore'] = (market_data['vix'] - market_data['vix'].rolling(90).mean()) / (market_data['vix'].rolling(90).std() + 1e-6)
            
            # Price momentum features
            features['returns_5d'] = market_data['returns'].rolling(5).sum()
            features['returns_10d'] = market_data['returns'].rolling(10).sum()
            features['realized_vol'] = market_data['realized_vol']
            features['vol_acceleration'] = market_data['realized_vol'].diff(5)
            
            # Volume features
            features['volume_change'] = market_data['volume'].pct_change(5)
            features['volume_zscore'] = (market_data['volume'] - market_data['volume'].rolling(90).mean()) / (market_data['volume'].rolling(90).std() + 1e-6)
            
            print(f"  ✓ Created {len(features.columns)} market-only features")
            return features
        
        # Original trends-based features
        features = pd.DataFrame(index=trends_data.index)
        
        for keyword in trends_data.columns:
            raw = trends_data[keyword]
            
            # 1. RATE OF CHANGE (key predictor!)
            features[f'{keyword}_roc_7d'] = raw.pct_change(7)
            features[f'{keyword}_roc_14d'] = raw.pct_change(14)
            
            # 2. ACCELERATION (is change speeding up?)
            roc = raw.pct_change(7)
            features[f'{keyword}_acceleration'] = roc.diff(7)
            
            # 3. Z-SCORE (how unusual is current level?)
            rolling_mean = raw.rolling(90).mean()
            rolling_std = raw.rolling(90).std()
            features[f'{keyword}_zscore'] = (raw - rolling_mean) / (rolling_std + 1e-6)
            
            # 4. VOLATILITY REGIME (is search behavior erratic?)
            features[f'{keyword}_vol_7d'] = raw.rolling(7).std()
            features[f'{keyword}_vol_30d'] = raw.rolling(30).std()
            
            # 5. RELATIVE VOLATILITY (is volatility rising?)
            short_vol = raw.rolling(7).std()
            long_vol = raw.rolling(30).std()
            features[f'{keyword}_vol_ratio'] = short_vol / (long_vol + 1e-6)
        
        # 6. COMPOSITE INDICATORS
        fear_cols = [col for col in features.columns if 'roc' in col and any(k in col for k in ['crash', 'recession', 'crisis'])]
        if fear_cols:
            features['composite_fear_roc'] = features[fear_cols].mean(axis=1)
            features['composite_fear_acceleration'] = features['composite_fear_roc'].diff(7)
        
        # 7. DIVERGENCE INDICATOR (are multiple signals firing?)
        zscore_cols = [col for col in features.columns if 'zscore' in col]
        if len(zscore_cols) > 0:
            features['keywords_spiking'] = (features[zscore_cols] > 2).sum(axis=1)
            
        print(f"  ✓ Created {len(features.columns)} change-focused features")
        
        return features
    
    def create_regime_change_labels(self, market_data):
        """
        KEY IMPROVEMENT: Label TRANSITIONS not absolute levels
        """
        print("\nCreating REGIME CHANGE labels...")
        
        vix = market_data['vix']
        
        # Define regimes
        LOW_VIX = 20
        HIGH_VIX = 30
        
        # Current regime
        current_regime = pd.cut(vix, bins=[0, LOW_VIX, HIGH_VIX, 100], 
                                labels=['calm', 'elevated', 'fear'])
        
        # Future regime (5 days ahead)
        future_regime = current_regime.shift(-5)
        
        # Label = 1 if we're transitioning from calm/elevated to higher state
        regime_numeric = current_regime.map({'calm': 0, 'elevated': 1, 'fear': 2})
        future_regime_numeric = future_regime.map({'calm': 0, 'elevated': 1, 'fear': 2})
        
        transition_up = (future_regime_numeric > regime_numeric).astype(int)
        
        # Also label sharp VIX increases
        vix_change = vix.shift(-5) - vix
        sharp_increase = (vix_change > 5).astype(int)
        
        # Combined label
        labels = ((transition_up + sharp_increase) > 0).astype(int)
        
        positive_pct = labels.mean() * 100
        print(f"  ✓ {positive_pct:.1f}% of periods are regime transitions")
        
        return labels
    
    def prepare_training_data(self):
        """Prepare data with new methodology"""
        print("="*60)
        print("PREPARING V2 TRAINING DATA (Change-Focused)")
        print("="*60)
        
        # 1. Get market data (always works with our fixed YFinanceClient)
        self.market_data = self.fetch_market_data()
        
        # 2. Try to get Google Trends data with caching
        all_keywords = self.fear_keywords + self.transition_keywords
        trends_cache = self.model_dir / "google_trends_cache.pkl"
        
        try:
            # Try with very long cache TTL (30 days) to avoid rate limits
            self.trends_data = self.fetch_google_trends(all_keywords, cache_path=trends_cache, ttl_hours=720)
            
            if self.trends_data.empty:
                print("  ⚠ Google Trends unavailable, using market-only features")
                self.trends_data = None
        except Exception as e:
            print(f"  ⚠ Google Trends error: {e}, using market-only features")
            self.trends_data = None
        
        # 2. Normalize and align dates
        print("\nAligning market data...")
        
        # Remove timezone info and normalize
        # Convert to DatetimeIndex if needed, then ensure no timezone
        if not isinstance(self.market_data.index, pd.DatetimeIndex):
            self.market_data.index = pd.DatetimeIndex(self.market_data.index)
        
        if self.market_data.index.tz is not None:
            self.market_data.index = self.market_data.index.tz_localize(None)
        
        self.market_data.index = self.market_data.index.normalize()
        
        print(f"  Market: {len(self.market_data)} points from {self.market_data.index.min()} to {self.market_data.index.max()}")
        
        # If no trends data, skip alignment
        if self.trends_data is None:
            print("  Using market-only mode (no trends data)")
        else:
            print("\nAligning trends and market data...")
            self.trends_data.index = pd.to_datetime(self.trends_data.index).normalize()
            
            if hasattr(self.trends_data.index, 'tz') and self.trends_data.index.tz is not None:
                self.trends_data.index = self.trends_data.index.tz_localize(None)
            
            print(f"  Trends: {len(self.trends_data)} points from {self.trends_data.index.min()} to {self.trends_data.index.max()}")
        
        # Check if trends is weekly data
        if self.trends_data is not None and len(self.trends_data) < 200:
            print("  Detected weekly trends data - resampling market data to weekly...")
            
            market_weekly = self.market_data.resample('W-SUN').agg({
                'close': 'last',
                'volume': 'sum',
                'vix': 'mean',
                'returns': 'sum',
                'realized_vol': 'mean'
            }).dropna()
            
            trends_df = self.trends_data.reset_index()
            market_df = market_weekly.reset_index()
            
            trends_df.rename(columns={trends_df.columns[0]: 'date'}, inplace=True)
            market_df.rename(columns={market_df.columns[0]: 'date'}, inplace=True)
            
            # Ensure date columns are timezone-naive
            if hasattr(trends_df['date'].dtype, 'tz') and trends_df['date'].dt.tz is not None:
                trends_df['date'] = trends_df['date'].dt.tz_localize(None)
            if hasattr(market_df['date'].dtype, 'tz') and market_df['date'].dt.tz is not None:
                market_df['date'] = market_df['date'].dt.tz_localize(None)
            
            trends_df = trends_df.sort_values('date')
            market_df = market_df.sort_values('date')
            
            merged = pd.merge_asof(trends_df, market_df, on='date', direction='nearest', tolerance=pd.Timedelta('3d'))
            merged = merged.dropna(subset=['vix'])
            
            if len(merged) == 0:
                raise ValueError("No overlapping dates found")
            
            merged = merged.set_index('date')
            trend_cols = [col for col in merged.columns if col in self.trends_data.columns]
            market_cols = ['close', 'volume', 'vix', 'returns', 'realized_vol']
            
            self.trends_data = merged[trend_cols]
            self.market_data = merged[market_cols]
            
            print(f"  ✓ Aligned {len(merged)} weeks of data")
        elif self.trends_data is not None:
            # Daily data
            common_dates = self.trends_data.index.intersection(self.market_data.index)
            
            if len(common_dates) == 0:
                print("  No direct intersection - trying merge_asof...")
                
                trends_df = self.trends_data.reset_index()
                market_df = self.market_data.reset_index()
                
                trends_df.rename(columns={trends_df.columns[0]: 'date'}, inplace=True)
                market_df.rename(columns={market_df.columns[0]: 'date'}, inplace=True)
                
                # Ensure date columns are timezone-naive
                if hasattr(trends_df['date'].dtype, 'tz') and trends_df['date'].dt.tz is not None:
                    trends_df['date'] = trends_df['date'].dt.tz_localize(None)
                if hasattr(market_df['date'].dtype, 'tz') and market_df['date'].dt.tz is not None:
                    market_df['date'] = market_df['date'].dt.tz_localize(None)
                
                trends_df = trends_df.sort_values('date')
                market_df = market_df.sort_values('date')
                
                merged = pd.merge_asof(trends_df, market_df, on='date', direction='nearest', tolerance=pd.Timedelta('1d'))
                merged = merged.dropna(subset=['vix'])
                
                if len(merged) == 0:
                    raise ValueError("No overlapping dates found")
                
                merged = merged.set_index('date')
                trend_cols = [col for col in merged.columns if col in self.trends_data.columns]
                market_cols = ['close', 'volume', 'vix', 'returns', 'realized_vol']
                
                self.trends_data = merged[trend_cols]
                self.market_data = merged[market_cols]
                
                print(f"  ✓ Aligned {len(merged)} days using merge_asof")
            else:
                self.trends_data = self.trends_data.loc[common_dates]
                self.market_data = self.market_data.loc[common_dates]
                print(f"  ✓ Aligned {len(common_dates)} days")
        
        # 3. Create CHANGE features (with or without trends data)
        self.features = self.create_change_focused_features(self.trends_data, self.market_data)
        
        # 4. Create TRANSITION labels
        self.labels = self.create_regime_change_labels(self.market_data)
        
        # 5. Clean data
        print(f"\nBefore cleaning: {len(self.features)} samples")
        print(f"  NaN counts: {self.features.isna().sum().sum()}")
        
        # Replace infinities with NaN
        self.features = self.features.replace([np.inf, -np.inf], np.nan)
        
        # Forward/backward fill
        self.features = self.features.fillna(method='bfill', limit=5).fillna(method='ffill', limit=5)
        
        # Replace remaining NaN/inf with column median
        for col in self.features.columns:
            if self.features[col].isnull().any() or np.isinf(self.features[col]).any():
                median_val = self.features[col].replace([np.inf, -np.inf], np.nan).median()
                if np.isnan(median_val):
                    median_val = 0
                self.features[col] = self.features[col].replace([np.inf, -np.inf, np.nan], median_val)
        
        # Get valid indices
        valid_idx = self.features.index[~(self.features.isnull().any(axis=1) | np.isinf(self.features).any(axis=1))]
        valid_idx = valid_idx.intersection(self.labels.dropna().index)
        
        self.features = self.features.loc[valid_idx]
        self.labels = self.labels.loc[valid_idx]
        
        # Final check
        if np.isinf(self.features.values).any():
            self.features = self.features.replace([np.inf, -np.inf], 0)
        
        if len(self.features) == 0:
            raise ValueError("No valid samples after cleaning")
        
        print(f"After cleaning: {len(self.features)} samples, {len(self.features.columns)} features")
        print(f"\n✓ Ready: {len(self.features)} samples, {len(self.features.columns)} features")
        print("="*60)
        
        return self.features, self.labels
    
    def train_model(self, test_size=0.2):
        """Train with better calibration"""
        print("\nTRAINING V2 MODEL")
        print("-"*40)
        
        if self.features is None:
            print("Error: Run prepare_training_data() first")
            return None
        
        if len(self.features) < 10:
            print(f"Error: Only {len(self.features)} samples. Need at least 10.")
            return None
        
        # Adjust test size for small datasets
        if len(self.features) < 50:
            test_size = 0.1
            print(f"⚠️  Small dataset ({len(self.features)} samples), using {test_size*100:.0f}% test split")
        
        # Chronological split
        split_idx = int(len(self.features) * (1 - test_size))
        split_idx = max(1, split_idx)
        
        X_train = self.features.iloc[:split_idx]
        X_test = self.features.iloc[split_idx:]
        y_train = self.labels.iloc[:split_idx]
        y_test = self.labels.iloc[split_idx:]
        
        print(f"Training: {len(X_train)} samples ({y_train.mean():.1%} transitions)")
        print(f"Test: {len(X_test)} samples ({y_test.mean():.1%} transitions)")
        
        # Scale
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train
        print("\nTraining Random Forest...")
        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_split=30,
            min_samples_leaf=15,
            class_weight='balanced',
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        print(f"\nTraining accuracy: {train_score:.3f}")
        print(f"Test accuracy: {test_score:.3f}")
        
        self.model = model
        self.scaler = scaler
        
        return model, scaler
    
    def save_model(self):
        """Save trained model and scaler"""
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained yet")
        
        model_path = self.model_dir / "volatility_predictor_model.pkl"
        scaler_path = self.model_dir / "volatility_predictor_scaler.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"✓ Model saved to {model_path}")
        print(f"✓ Scaler saved to {scaler_path}")
    
    def load_model(self):
        """Load trained model and scaler"""
        model_path = self.model_dir / "volatility_predictor_model.pkl"
        scaler_path = self.model_dir / "volatility_predictor_scaler.pkl"
        
        if not model_path.exists() or not scaler_path.exists():
            return False
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        print(f"✓ Model loaded from {model_path}")
        return True
    
    def get_market_only_prediction(self) -> dict:
        """
        Fallback prediction using only market data (when Google Trends unavailable)
        """
        if self.market_data is None or len(self.market_data) == 0:
            raise ValueError("No market data available")
        
        latest = self.market_data.iloc[-1]
        vix = float(latest['vix']) if pd.notna(latest['vix']) else 20.0
        realized_vol = float(latest['realized_vol']) * 100 if pd.notna(latest['realized_vol']) else 15.0  # Convert to %
        
        # Calculate VP score based on VIX and realized vol
        # VIX scoring: 12=0pts, 20=40pts, 30=90pts, 35=100pts
        if vix < 15:
            vix_score = 0
        elif vix < 20:
            vix_score = (vix - 15) * 8  # 15-20 range = 0-40pts
        elif vix < 30:
            vix_score = 40 + (vix - 20) * 5  # 20-30 range = 40-90pts
        else:
            vix_score = min(100, 90 + (vix - 30) * 2)  # 30+ = 90-100pts
        
        # Realized vol scoring: < 15% = low, 15-25% = moderate, > 25% = high
        if realized_vol < 15:
            vol_score = 0
        elif realized_vol < 25:
            vol_score = (realized_vol - 15) * 6  # 15-25 range = 0-60pts
        else:
            vol_score = min(100, 60 + (realized_vol - 25) * 4)  # 25+ = 60-100pts
        
        # Calculate VIX momentum (is it rising?)
        vix_5d_change = float(self.market_data['vix'].pct_change(5).iloc[-1]) if pd.notna(self.market_data['vix'].pct_change(5).iloc[-1]) else 0
        if vix_5d_change > 0.3:  # 30% increase
            momentum_score = 100
        elif vix_5d_change > 0.1:  # 10-30% increase
            momentum_score = (vix_5d_change - 0.1) * 500  # Scale to 0-100
        elif vix_5d_change > -0.1:  # -10 to +10%
            momentum_score = 0
        else:  # Falling VIX = negative risk
            momentum_score = 0
        
        # Weighted combination
        vp_score = int(0.5 * vix_score + 0.3 * vol_score + 0.2 * momentum_score)
        
        # Confidence based on how extreme the values are
        confidence = int(min(100, max(20, abs(vp_score - 50) * 2)))
        
        return {
            "vp_score": vp_score,
            "confidence": confidence,
            "spike_probability": vp_score / 100.0,
            "signal_strength": vp_score,
            "last_updated": datetime.now().isoformat(),
            "components": {
                "vix_level": int(vix_score),
                "realized_vol": int(vol_score),
                "momentum": int(momentum_score)
            },
            "current_values": {
                "vix": round(vix, 2),
                "realized_vol_pct": round(realized_vol, 2),
                "vix_5d_change_pct": round(vix_5d_change * 100, 2)
            },
            "prediction_window_days": "2-5",
            "mode": "market-only-fallback"
        }
    
    def get_current_prediction(self) -> dict:
        """
        Get current volatility prediction as JSON
        
        Returns:
            dict with VP score, confidence, components, etc.
        """
        if self.model is None or self.scaler is None:
            # Try to load saved model
            if not self.load_model():
                raise ValueError("Model not trained. Run train_model() first or train with --mode train")
        
        if self.features is None or len(self.features) == 0:
            raise ValueError("Features not prepared. Run prepare_training_data() first")
        
        # Check if features match model expectations
        if self.features.shape[1] != self.scaler.n_features_in_:
            print(f"  ⚠ Feature mismatch: got {self.features.shape[1]} features, model expects {self.scaler.n_features_in_}")
            print(f"  Using market-only fallback prediction")
            return self.get_market_only_prediction()
        
        # Get latest features
        latest_features = self.features.iloc[-1:].values
        latest_features_scaled = self.scaler.transform(latest_features)
        
        # Get prediction probability
        try:
            proba = self.model.predict_proba(latest_features_scaled)[0]
            # Check if model learned both classes
            if len(proba) > 1:
                probability = proba[1]
            else:
                # Only one class learned (no volatility spikes in training data)
                print(f"  ⚠ Model only learned one class, using market-only fallback")
                return self.get_market_only_prediction()
        except Exception as e:
            print(f"  ⚠ Prediction error: {e}, using market-only fallback")
            return self.get_market_only_prediction()
        
        # Calculate VP score (0-100)
        vp_score = int(probability * 100)
        
        # Calculate signal strength (based on percentile)
        all_probs = self.model.predict_proba(self.scaler.transform(self.features))[:, 1]
        percentile = (all_probs < probability).mean() * 100
        signal_strength = int(percentile)
        
        # Calculate confidence (based on model certainty)
        confidence = int(abs(probability - 0.5) * 200)  # 0-100 scale
        
        # Get component scores
        latest_row = self.features.iloc[-1]
        components = {}
        
        if 'composite_fear_roc' in latest_row.index:
            fear_composite = latest_row['composite_fear_roc']
            components['fear_composite'] = int(np.clip(fear_composite * 100, 0, 100))
        
        # Calculate search volatility score
        vol_cols = [col for col in latest_row.index if 'vol_ratio' in col]
        if vol_cols:
            avg_vol_ratio = latest_row[vol_cols].mean()
            components['search_volatility'] = int(np.clip(avg_vol_ratio * 50, 0, 100))
        
        # Cross-asset stress (placeholder - would need additional data)
        components['cross_asset_stress'] = 70  # Default for now
        
        # Spike probability (2-5 day window)
        spike_probability = float(probability)
        
        return {
            "vp_score": vp_score,
            "confidence": confidence,
            "spike_probability": spike_probability,
            "signal_strength": signal_strength,
            "last_updated": datetime.now().isoformat(),
            "components": components,
            "prediction_window_days": "2-5"
        }
    
    def predict_with_dynamic_threshold(self, percentile=80):
        """Use dynamic threshold for predictions"""
        if not hasattr(self, 'model') or self.model is None:
            print("Error: Train model first")
            return None
        
        X_scaled = self.scaler.transform(self.features)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        threshold = np.percentile(probabilities, percentile)
        predictions_binary = (probabilities > threshold).astype(int)
        
        return probabilities, predictions_binary, threshold


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Volatility Predictor V2')
    parser.add_argument('--mode', choices=['json', 'train'], default='json',
                       help='Mode: json (output prediction) or train (retrain model)')
    parser.add_argument('--model-dir', default='data/cache/models',
                       help='Directory to save/load models')
    
    args = parser.parse_args()
    
    predictor = VolatilityPredictorV2(model_dir=args.model_dir)
    
    if args.mode == 'train':
        try:
            # Prepare and train
            predictor.prepare_training_data()
            predictor.train_model()
            predictor.save_model()
            print("\n✓ Training complete!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    
    elif args.mode == 'json':
        try:
            # Load model or prepare data if needed
            if not predictor.load_model():
                print("Model not found. Preparing data and training...")
                predictor.prepare_training_data()
                predictor.train_model()
                predictor.save_model()
            
            # Ensure we have features
            if predictor.features is None or len(predictor.features) == 0:
                predictor.prepare_training_data()
            
            # Get prediction
            result = predictor.get_current_prediction()
            
            # Output JSON to stdout
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "vp_score": None,
                "last_updated": datetime.now().isoformat()
            }
            print(json.dumps(error_result, indent=2))
            exit(1)


if __name__ == "__main__":
    main()


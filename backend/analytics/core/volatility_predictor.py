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
        
        # Storage
        self.trends_data = None
        self.market_data = None
        self.features = None
        self.labels = None
        self.model = None
        self.scaler = None
        
    def fetch_google_trends(self, keywords, timeframe='today 5-y'):
        """Fetch Google Trends data"""
        print(f"Fetching Google Trends data for {len(keywords)} keywords...")
        
        all_trends = pd.DataFrame()
        
        for i in range(0, len(keywords), 5):
            batch = keywords[i:i+5]
            
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
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
        
        return all_trends
    
    def fetch_market_data(self, ticker='^GSPC', vix_ticker='^VIX', period='5y'):
        """Fetch market data"""
        print(f"\nFetching market data...")
        
        market = yf.download(ticker, period=period, progress=False)
        vix = yf.download(vix_ticker, period=period, progress=False)
        
        market_data = pd.DataFrame()
        market_data['close'] = market['Close']
        market_data['volume'] = market['Volume']
        market_data['vix'] = vix['Close']
        market_data['returns'] = market_data['close'].pct_change()
        market_data['realized_vol'] = market_data['returns'].rolling(20).std() * np.sqrt(252)
        
        print(f"  ✓ Fetched {len(market_data)} days")
        
        return market_data
    
    def create_change_focused_features(self, trends_data):
        """
        KEY IMPROVEMENT: Focus on CHANGES and ACCELERATION
        """
        print("\nCreating CHANGE-FOCUSED features...")
        
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
        
        # 1. Get data
        all_keywords = self.fear_keywords + self.transition_keywords
        self.trends_data = self.fetch_google_trends(all_keywords)
        self.market_data = self.fetch_market_data()
        
        # 2. Normalize and align dates
        print("\nAligning trends and market data...")
        
        self.trends_data.index = pd.to_datetime(self.trends_data.index).normalize()
        self.market_data.index = pd.to_datetime(self.market_data.index).normalize()
        
        # Remove timezone info if present
        if hasattr(self.market_data.index, 'tz') and self.market_data.index.tz is not None:
            self.market_data.index = self.market_data.index.tz_localize(None)
        if hasattr(self.trends_data.index, 'tz') and self.trends_data.index.tz is not None:
            self.trends_data.index = self.trends_data.index.tz_localize(None)
        
        print(f"  Trends: {len(self.trends_data)} points from {self.trends_data.index.min()} to {self.trends_data.index.max()}")
        print(f"  Market: {len(self.market_data)} points from {self.market_data.index.min()} to {self.market_data.index.max()}")
        
        # Check if trends is weekly data
        if len(self.trends_data) < 200:
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
        else:
            # Daily data
            common_dates = self.trends_data.index.intersection(self.market_data.index)
            
            if len(common_dates) == 0:
                print("  No direct intersection - trying merge_asof...")
                
                trends_df = self.trends_data.reset_index()
                market_df = self.market_data.reset_index()
                
                trends_df.rename(columns={trends_df.columns[0]: 'date'}, inplace=True)
                market_df.rename(columns={market_df.columns[0]: 'date'}, inplace=True)
                
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
        
        # 3. Create CHANGE features
        self.features = self.create_change_focused_features(self.trends_data)
        
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
        
        # Get latest features
        latest_features = self.features.iloc[-1:].values
        latest_features_scaled = self.scaler.transform(latest_features)
        
        # Get prediction probability
        probability = self.model.predict_proba(latest_features_scaled)[0, 1]
        
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


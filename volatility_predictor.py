"""
Volatility Spike Predictor V2
Improvements over V1:
1. Dynamic thresholds instead of fixed 50%
2. Focus on CHANGES in risk, not absolute levels
3. Better false positive filtering
4. Regime change detection
5. Multi-timeframe analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from pytrends.request import TrendReq
    import yfinance as yf
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import matplotlib.pyplot as plt
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
    
    def __init__(self):
        """Initialize with improved keyword selection"""
        
        # Refined keywords - remove terms that cause false positives
        self.fear_keywords = [
            'stock market crash',
            'recession',
            'financial crisis',
            'market crash'  # More specific than just "debt"
        ]
        
        # Add keywords that spike during TRANSITIONS
        self.transition_keywords = [
            'buy puts',  # Options activity spikes when fear rises
            'market correction',
            'volatility index',
            'sell stocks'  # Action-oriented searches
        ]
        
        self.pytrends = TrendReq(hl='en-US', tz=360)
        
        # Storage
        self.trends_data = None
        self.market_data = None
        self.features = None
        self.labels = None
        
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
        
        The problem with V1 was it looked at absolute levels.
        This version looks at:
        1. Rate of change (is fear rising?)
        2. Acceleration (is the rise accelerating?)
        3. Divergence (are different keywords spiking together?)
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
            # Count how many keywords have z-score > 2 (unusual activity)
            features['keywords_spiking'] = (features[zscore_cols] > 2).sum(axis=1)
            
        print(f"  ✓ Created {len(features.columns)} change-focused features")
        
        return features
    
    def create_regime_change_labels(self, market_data):
        """
        KEY IMPROVEMENT: Label TRANSITIONS not absolute levels
        
        Instead of labeling "VIX > 25" (persistent state),
        label "VIX about to spike from calm to elevated" (transition)
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
        sharp_increase = (vix_change > 5).astype(int)  # VIX jumping 5+ points
        
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
        
        # 2. Normalize and align dates (improved from V1)
        print("\nAligning trends and market data...")
        
        # Normalize indices to dates without time components
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
        
        # 3. Create CHANGE features (not level features)
        self.features = self.create_change_focused_features(self.trends_data)
        
        # 4. Create TRANSITION labels (not level labels)
        self.labels = self.create_regime_change_labels(self.market_data)
        
        # 5. Clean data - handle NaN and infinity
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
        
        # Train with adjusted parameters
        print("\nTraining Random Forest...")
        model = RandomForestClassifier(
            n_estimators=150,  # More trees
            max_depth=8,  # Shallower to reduce overfitting
            min_samples_split=30,  # Require more samples
            min_samples_leaf=15,  # More conservative splits
            class_weight='balanced',
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        print(f"\nTraining accuracy: {train_score:.3f}")
        print(f"Test accuracy: {test_score:.3f}")
        
        # Probabilities on test set
        test_probs = model.predict_proba(X_test_scaled)[:, 1]
        
        # Show distribution of predicted probabilities
        print("\nPredicted Probability Distribution:")
        print(f"  Mean: {test_probs.mean():.3f}")
        print(f"  Median: {np.median(test_probs):.3f}")
        print(f"  75th percentile: {np.percentile(test_probs, 75):.3f}")
        print(f"  90th percentile: {np.percentile(test_probs, 90):.3f}")
        
        # Feature importance
        importance = pd.DataFrame({
            'feature': self.features.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Features:")
        print(importance.head(10).to_string(index=False))
        
        self.model = model
        self.scaler = scaler
        
        return model, scaler
    
    def predict_with_dynamic_threshold(self, percentile=80):
        """
        KEY IMPROVEMENT: Use dynamic threshold
        
        Instead of >50% = high risk, use >80th percentile = high risk
        This dramatically reduces false positives
        """
        if not hasattr(self, 'model'):
            print("Error: Train model first")
            return None
        
        # Get predictions for all data
        X_scaled = self.scaler.transform(self.features)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        # Calculate dynamic threshold
        threshold = np.percentile(probabilities, percentile)
        
        print(f"\nDynamic threshold ({percentile}th percentile): {threshold:.3f}")
        
        # Binary predictions with this threshold
        predictions_binary = (probabilities > threshold).astype(int)
        
        print(f"High risk periods: {predictions_binary.sum()} days ({predictions_binary.mean():.1%})")
        
        return probabilities, predictions_binary, threshold
    
    def plot_improved_results(self, percentile=80):
        """Plot with improved thresholding"""
        if not hasattr(self, 'model'):
            print("Error: Train model first")
            return
        
        probabilities, predictions_binary, threshold = self.predict_with_dynamic_threshold(percentile)
        
        fig, axes = plt.subplots(4, 1, figsize=(15, 12))
        
        # Plot 1: VIX and Model Risk (showing threshold)
        ax1 = axes[0]
        ax1.plot(self.market_data.index, self.market_data['vix'], 
                label='VIX (Actual)', color='red', alpha=0.7, linewidth=1.5)
        
        ax1_twin = ax1.twinx()
        ax1_twin.plot(self.features.index, probabilities * 100,
                     label='Model Risk Score', color='blue', alpha=0.5, linewidth=1)
        ax1_twin.axhline(threshold * 100, color='orange', linestyle='--', 
                        alpha=0.5, label=f'{percentile}th Percentile Threshold')
        
        ax1.axhline(25, color='red', linestyle='--', alpha=0.3)
        ax1.set_ylabel('VIX Level', color='red')
        ax1_twin.set_ylabel('Model Risk Score (0-100)', color='blue')
        ax1.set_title('VIX vs Model Predictions (V2 - Change Focused)')
        ax1.legend(loc='upper left')
        ax1_twin.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: S&P 500 with HIGH-THRESHOLD predictions
        ax2 = axes[1]
        ax2.plot(self.market_data.index, self.market_data['close'], 
                label='S&P 500', color='green', linewidth=1.5)
        
        # Highlight only HIGH probability periods
        for idx in self.features.index[predictions_binary == 1]:
            ax2.axvspan(idx, idx + timedelta(days=1), alpha=0.3, color='red')
        
        ax2.set_ylabel('S&P 500 Price')
        ax2.set_title(f'S&P 500 with High-Risk Warnings (>{percentile}th Percentile)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Rate of Change in Fear Indicator
        ax3 = axes[2]
        if 'composite_fear_roc' in self.features.columns:
            ax3.plot(self.features.index, self.features['composite_fear_roc'],
                    label='Fear Rate of Change', color='orange', linewidth=1)
            ax3.axhline(0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
            ax3.fill_between(self.features.index, 0, self.features['composite_fear_roc'],
                           where=self.features['composite_fear_roc'] > 0,
                           alpha=0.3, color='red', label='Increasing Fear')
            ax3.fill_between(self.features.index, 0, self.features['composite_fear_roc'],
                           where=self.features['composite_fear_roc'] < 0,
                           alpha=0.3, color='green', label='Decreasing Fear')
        ax3.set_ylabel('Rate of Change')
        ax3.set_title('Change in Fear Indicator (Not Absolute Level)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Prediction Performance Analysis
        ax4 = axes[3]
        
        # Calculate forward VIX changes
        vix_aligned = self.market_data.loc[self.features.index, 'vix']
        forward_vix_change = vix_aligned.shift(-5) - vix_aligned
        
        # Compare predictions vs actual changes
        correct_predictions = []
        for idx, pred in zip(self.features.index, predictions_binary):
            if idx in forward_vix_change.index:
                actual_change = forward_vix_change.loc[idx]
                # Prediction correct if we predicted high risk and VIX increased >3 points
                if pred == 1:
                    correct_predictions.append(1 if actual_change > 3 else 0)
        
        if correct_predictions:
            accuracy = np.mean(correct_predictions)
            ax4.text(0.5, 0.5, f'Precision on High-Risk Warnings: {accuracy:.1%}',
                    ha='center', va='center', fontsize=16, 
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')
            ax4.set_title('Model Performance')
        
        plt.tight_layout()
        
        # Save with cross-platform path
        import os
        output_file = os.path.join(os.getcwd(), 'volatility_prediction_v2.png')
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\n✓ V2 chart saved to: {output_file}")
        
        return fig


def main():
    """Run improved version"""
    print("""
╔════════════════════════════════════════════════════════════╗
║   VOLATILITY PREDICTOR V2                                 ║
║   Focus: REGIME CHANGES not absolute levels               ║
║   Improvement: Dynamic thresholds, fewer false positives  ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    predictor = VolatilityPredictorV2()
    
    try:
        # Prepare data
        features, labels = predictor.prepare_training_data()
        
        # Train
        model, scaler = predictor.train_model()
        
        # Plot with 80th percentile threshold (vs 50% in V1)
        predictor.plot_improved_results(percentile=80)
        
        print("\n" + "="*60)
        print("V2 IMPROVEMENTS")
        print("="*60)
        print("1. ✓ Features focus on CHANGES not levels")
        print("2. ✓ Labels focus on TRANSITIONS not persistent states")
        print("3. ✓ Dynamic threshold (80th percentile) vs fixed 50%")
        print("4. ✓ Should see FAR fewer false positives")
        print("\nCompare outputs:")
        print("  V1: volatility_prediction.png")
        print("  V2: volatility_prediction_v2.png")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

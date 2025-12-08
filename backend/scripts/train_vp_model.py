#!/usr/bin/env python3
"""
Script to train the Volatility Predictor model
Run this weekly to retrain the model with latest data
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from analytics.core.volatility_predictor import VolatilityPredictorV2


def main():
    print("=" * 60)
    print("Training Volatility Predictor Model")
    print("=" * 60)
    
    predictor = VolatilityPredictorV2()
    
    try:
        # Prepare data
        print("\nStep 1: Preparing training data...")
        predictor.prepare_training_data()
        
        # Train model
        print("\nStep 2: Training model...")
        predictor.train_model()
        
        # Save model
        print("\nStep 3: Saving model...")
        predictor.save_model()
        
        print("\n" + "=" * 60)
        print("✓ Training complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


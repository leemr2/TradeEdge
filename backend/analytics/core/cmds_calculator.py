"""
Combined Market Danger Score (CMDS) Calculator
Combines Fundamental Risk Score (FRS) and Volatility Predictor (VP)
CMDS = (0.65 × FRS) + (0.35 × VP)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directories to path for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from analytics.core.frs_calculator import FRSCalculator
from analytics.core.volatility_predictor import VolatilityPredictorV2


class CMDSCalculator:
    """Calculate Combined Market Danger Score"""
    
    def __init__(self, 
                 frs_weight: float = 0.65,
                 vp_weight: float = 0.35,
                 fred_api_key: Optional[str] = None):
        """
        Initialize CMDS calculator
        
        Args:
            frs_weight: Weight for Fundamental Risk Score (default 0.65)
            vp_weight: Weight for Volatility Predictor (default 0.35)
            fred_api_key: FRED API key for FRS calculator
        """
        if abs(frs_weight + vp_weight - 1.0) > 0.01:
            raise ValueError("FRS and VP weights must sum to 1.0")
        
        self.frs_weight = frs_weight
        self.vp_weight = vp_weight
        
        self.frs_calculator = FRSCalculator(fred_api_key=fred_api_key)
        self.vp_predictor = VolatilityPredictorV2()
    
    def get_zone(self, cmds: float) -> str:
        """Determine allocation zone from CMDS score"""
        if cmds <= 25:
            return "SAFE"
        elif cmds <= 45:
            return "CAUTIOUS"
        elif cmds <= 65:
            return "ELEVATED"
        elif cmds <= 80:
            return "HIGH"
        else:
            return "EXTREME"
    
    def get_allocation(self, zone: str) -> Dict[str, tuple]:
        """Get recommended allocation ranges for zone"""
        allocations = {
            "SAFE": {
                "equity_pct": (90, 100),
                "hedge_pct": (0, 2),
                "cash_pct": (0, 10)
            },
            "CAUTIOUS": {
                "equity_pct": (70, 90),
                "hedge_pct": (2, 5),
                "cash_pct": (10, 20)
            },
            "ELEVATED": {
                "equity_pct": (50, 70),
                "hedge_pct": (5, 10),
                "cash_pct": (20, 35)
            },
            "HIGH": {
                "equity_pct": (30, 50),
                "hedge_pct": (10, 15),
                "cash_pct": (35, 50)
            },
            "EXTREME": {
                "equity_pct": (10, 30),
                "hedge_pct": (15, 25),
                "cash_pct": (50, 75)
            }
        }
        return allocations.get(zone, allocations["CAUTIOUS"])
    
    def interpret_divergence(self, frs: float, vp: float) -> str:
        """
        Interpret divergence between FRS and VP
        
        Returns:
            Interpretation string
        """
        divergence = abs(frs - vp)
        
        if divergence > 40:
            if frs > vp:
                return "COILED_SPRING: Structural risk high, catalyst not yet present"
            else:
                return "FALSE_ALARM: Short-term panic in stable environment"
        elif frs > 70 and vp > 70:
            return "ALIGNED_DANGER: Both signals confirm high risk"
        elif frs < 40 and vp < 40:
            return "ALL_CLEAR: Healthy environment"
        else:
            return "MIXED: Monitor for clarity"
    
    def calculate_cmds(self) -> Dict[str, Any]:
        """
        Calculate Combined Market Danger Score
        
        Returns:
            dict with CMDS score, zone, allocation, interpretation, etc.
        """
        print("Calculating Combined Market Danger Score...")
        
        # Get FRS
        try:
            frs_result = self.frs_calculator.calculate_frs()
            frs_score = frs_result["frs_score"]
        except Exception as e:
            print(f"Error calculating FRS: {e}")
            frs_score = 0.0
            frs_result = {"frs_score": 0.0, "error": str(e)}
        
        # Get VP
        try:
            # Try to load model first
            if not self.vp_predictor.load_model():
                print("VP model not found. Using default score.")
                vp_score = 50.0  # Default moderate score
            else:
                # Ensure we have features
                if self.vp_predictor.features is None or len(self.vp_predictor.features) == 0:
                    print("Preparing VP data...")
                    self.vp_predictor.prepare_training_data()
                
                vp_result = self.vp_predictor.get_current_prediction()
                vp_score = vp_result["vp_score"]
        except Exception as e:
            print(f"Error calculating VP: {e}")
            vp_score = 50.0  # Default moderate score
            vp_result = {"vp_score": 50.0, "error": str(e)}
        
        # Calculate CMDS
        cmds = (self.frs_weight * frs_score) + (self.vp_weight * vp_score)
        cmds = max(0, min(100, cmds))  # Clamp to 0-100
        
        # Determine zone
        zone = self.get_zone(cmds)
        
        # Get allocation recommendations
        allocation = self.get_allocation(zone)
        
        # Calculate divergence
        divergence = abs(frs_score - vp_score)
        interpretation = self.interpret_divergence(frs_score, vp_score)
        
        return {
            "cmds": round(cmds, 1),
            "zone": zone,
            "last_updated": datetime.now().isoformat(),
            "components": {
                "frs": round(frs_score, 1),
                "frs_contribution": round(self.frs_weight * frs_score, 1),
                "vp": round(vp_score, 1),
                "vp_contribution": round(self.vp_weight * vp_score, 1)
            },
            "allocation": {
                "equity_pct": list(allocation["equity_pct"]),
                "hedge_pct": list(allocation["hedge_pct"]),
                "cash_pct": list(allocation["cash_pct"])
            },
            "divergence": round(divergence, 1),
            "interpretation": interpretation,
            "weights": {
                "frs_weight": self.frs_weight,
                "vp_weight": self.vp_weight
            },
            "frs_details": frs_result if "error" not in frs_result else None,
            "vp_details": vp_result if "error" not in vp_result else None
        }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Combined Market Danger Score Calculator')
    parser.add_argument('--frs-weight', type=float, default=0.65,
                       help='Weight for FRS (default 0.65)')
    parser.add_argument('--vp-weight', type=float, default=0.35,
                       help='Weight for VP (default 0.35)')
    parser.add_argument('--fred-key', help='FRED API key (or set FRED_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Validate weights
    if abs(args.frs_weight + args.vp_weight - 1.0) > 0.01:
        print("Error: FRS and VP weights must sum to 1.0")
        exit(1)
    
    calculator = CMDSCalculator(
        frs_weight=args.frs_weight,
        vp_weight=args.vp_weight,
        fred_api_key=args.fred_key
    )
    
    try:
        result = calculator.calculate_cmds()
        print(json.dumps(result, indent=2))
    except Exception as e:
        error_result = {
            "error": str(e),
            "cmds": None,
            "last_updated": datetime.now().isoformat()
        }
        print(json.dumps(error_result, indent=2))
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()


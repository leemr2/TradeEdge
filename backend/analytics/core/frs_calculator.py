"""
Fundamental Risk Score (FRS) Calculator
Calculates market risk based on 5 categories:
1. Macro/Cycle (0-30 points)
2. Valuation (0-25 points)
3. Leverage & Stability (0-25 points)
4. Earnings (0-10 points)
5. Sentiment (-10 to +10 points)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from backend directory
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv not installed, will use system env vars

# Add parent directories to path for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from analytics.data_fetchers.fred_client import FredClient
from analytics.data_fetchers.yfinance_client import YFinanceClient
from analytics.core.manual_inputs import load_manual_inputs
from analytics.core.categories import (
    MacroCycleCategory,
    ValuationCategory,
    LeverageStabilityCategory,
    EarningsMarginsCategory,
    SentimentCategory
)


class FRSCalculator:
    """Calculate Fundamental Risk Score"""
    
    def __init__(self, fred_api_key: Optional[str] = None, manual_inputs: Optional[Dict[str, Any]] = None):
        """Initialize FRS calculator with data clients"""
        self.fred = FredClient(api_key=fred_api_key)
        self.yfinance = YFinanceClient()
        
        # Load manual inputs from config file or use provided
        if manual_inputs is None:
            self.manual_inputs = load_manual_inputs()
        else:
            self.manual_inputs = manual_inputs
        
        # Initialize category calculators
        self.macro_category = MacroCycleCategory(
            fred_client=self.fred,
            yfinance_client=self.yfinance,
            manual_inputs=self.manual_inputs
        )
        self.valuation_category = ValuationCategory(
            fred_client=self.fred,
            yfinance_client=self.yfinance,
            manual_inputs=self.manual_inputs
        )
        self.leverage_category = LeverageStabilityCategory(
            fred_client=self.fred,
            yfinance_client=self.yfinance,
            manual_inputs=self.manual_inputs
        )
        self.earnings_category = EarningsMarginsCategory(
            fred_client=self.fred,
            yfinance_client=self.yfinance,
            manual_inputs=self.manual_inputs
        )
        self.sentiment_category = SentimentCategory(
            fred_client=self.fred,
            yfinance_client=self.yfinance,
            manual_inputs=self.manual_inputs
        )
    
    def calculate_frs(self) -> Dict[str, Any]:
        """
        Calculate complete Fundamental Risk Score
        
        Returns:
            dict with FRS score, breakdown, correction probability, etc.
        """
        print("Calculating Fundamental Risk Score...")
        
        # Calculate each category
        macro_result = self.macro_category.calculate()
        valuation_result = self.valuation_category.calculate()
        leverage_result = self.leverage_category.calculate()
        earnings_result = self.earnings_category.calculate()
        sentiment_result = self.sentiment_category.calculate()
        
        # Extract scores
        macro_score = macro_result['score']
        valuation_score = valuation_result['score']
        leverage_score = leverage_result['score']
        earnings_score = earnings_result['score']
        sentiment_score = sentiment_result['score']
        
        # Total Risk Score
        total_score = macro_score + valuation_score + leverage_score + earnings_score + sentiment_score
        total_score = max(0, min(100, total_score))  # Clamp to 0-100
        
        # Calculate correction probability
        correction_prob = 15 + (0.8 * total_score)
        correction_prob = max(5, min(95, correction_prob))  # Clamp to 5-95%
        
        # Determine zone
        if total_score <= 30:
            zone = "GREEN"
        elif total_score <= 50:
            zone = "YELLOW"
        elif total_score <= 70:
            zone = "ORANGE"
        elif total_score <= 85:
            zone = "RED"
        else:
            zone = "BLACK"
        
        # Build component details for backward compatibility
        component_details = {}
        for category_result in [macro_result, valuation_result, leverage_result, earnings_result, sentiment_result]:
            for comp_name, comp_data in category_result.get('components', {}).items():
                component_details[comp_name] = comp_data.get('score', 0.0)
        
        # Build detailed categories structure
        categories = {
            'macro_cycle': {
                'score': macro_score,
                'max': 30.0,
                'components': macro_result['components'],
                'metadata': {
                    'name': macro_result['metadata'].name,
                    'description': macro_result['metadata'].description,
                    'update_frequency': macro_result['metadata'].update_frequency,
                    'data_sources': macro_result['metadata'].data_sources,
                    'next_update': macro_result['metadata'].next_update,
                }
            },
            'valuation': {
                'score': valuation_score,
                'max': 25.0,
                'components': valuation_result['components'],
                'metadata': {
                    'name': valuation_result['metadata'].name,
                    'description': valuation_result['metadata'].description,
                    'update_frequency': valuation_result['metadata'].update_frequency,
                    'data_sources': valuation_result['metadata'].data_sources,
                    'next_update': valuation_result['metadata'].next_update,
                }
            },
            'leverage_stability': {
                'score': leverage_score,
                'max': 25.0,
                'components': leverage_result['components'],
                'metadata': {
                    'name': leverage_result['metadata'].name,
                    'description': leverage_result['metadata'].description,
                    'update_frequency': leverage_result['metadata'].update_frequency,
                    'data_sources': leverage_result['metadata'].data_sources,
                    'next_update': leverage_result['metadata'].next_update,
                }
            },
            'earnings_margins': {
                'score': earnings_score,
                'max': 10.0,
                'components': earnings_result['components'],
                'metadata': {
                    'name': earnings_result['metadata'].name,
                    'description': earnings_result['metadata'].description,
                    'update_frequency': earnings_result['metadata'].update_frequency,
                    'data_sources': earnings_result['metadata'].data_sources,
                    'next_update': earnings_result['metadata'].next_update,
                }
            },
            'sentiment': {
                'score': sentiment_score,
                'max': 10.0,
                'min': -10.0,
                'components': sentiment_result['components'],
                'metadata': {
                    'name': sentiment_result['metadata'].name,
                    'description': sentiment_result['metadata'].description,
                    'update_frequency': sentiment_result['metadata'].update_frequency,
                    'data_sources': sentiment_result['metadata'].data_sources,
                    'next_update': sentiment_result['metadata'].next_update,
                }
            }
        }
        
        # Build manual inputs structure with metadata
        manual_inputs_structured = {}
        if 'hedge_fund_leverage' in self.manual_inputs:
            manual_inputs_structured['hedge_fund_leverage'] = {
                'value': self.manual_inputs['hedge_fund_leverage'],
                'as_of': self.manual_inputs.get('hedge_fund_leverage_as_of', None),
                'next_update': '2026-05-01 (Next Fed FSR)'
            }
        if 'cre_delinquency_rate' in self.manual_inputs:
            manual_inputs_structured['cre_delinquency_rate'] = {
                'value': self.manual_inputs['cre_delinquency_rate'],
                'as_of': self.manual_inputs.get('cre_delinquency_as_of', None),
                'next_update': '2026-02-15 (Next FDIC QBP)'
            }
        
        return {
            "frs_score": round(total_score, 1),
            "correction_probability": round(correction_prob / 100, 3),
            "last_updated": datetime.now().isoformat(),
            "breakdown": {
                "macro": round(macro_score, 1),
                "valuation": round(valuation_score, 1),
                "leverage": round(leverage_score, 1),
                "earnings": round(earnings_score, 1),
                "sentiment": round(sentiment_score, 1)
            },
            "zone": zone,
            "data_sources": ["FRED", "yfinance"],
            "manual_inputs": self.manual_inputs,  # Backward compatibility
            "component_details": component_details,  # Backward compatibility
            # New detailed structure
            "categories": categories,
            "manual_inputs_structured": manual_inputs_structured,
        }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fundamental Risk Score Calculator')
    parser.add_argument('--fred-key', help='FRED API key (or set FRED_API_KEY env var)')
    
    args = parser.parse_args()
    
    calculator = FRSCalculator(fred_api_key=args.fred_key)
    
    try:
        result = calculator.calculate_frs()
        print(json.dumps(result, indent=2))
    except Exception as e:
        error_result = {
            "error": str(e),
            "frs_score": None,
            "last_updated": datetime.now().isoformat()
        }
        print(json.dumps(error_result, indent=2))
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()


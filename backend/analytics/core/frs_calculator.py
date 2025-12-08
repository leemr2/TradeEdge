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


class FRSCalculator:
    """Calculate Fundamental Risk Score"""
    
    def __init__(self, fred_api_key: Optional[str] = None):
        """Initialize FRS calculator with data clients"""
        self.fred = FredClient(api_key=fred_api_key)
        self.yfinance = YFinanceClient()
        
        # Manual inputs (from Fed reports, etc.)
        self.manual_inputs = {
            'hedge_fund_leverage': 10,  # 0-10 scale, default high
            'cre_delinquency_rate': 5.0,  # Percentage, default moderate
        }
    
    def score_unemployment_trend(self) -> float:
        """
        Category 1.1: Unemployment Trend (0-10 points)
        0 points: Flat or falling, ≤4%
        5 points: Up 0.5-0.9pp from trough
        10 points: Up ≥1.0pp from trough (Sahm rule trigger)
        """
        try:
            unrate = self.fred.fetch_series('UNRATE', start_date='2020-01-01')
            
            if len(unrate) < 12:
                return 0.0
            
            # Get 12-month low
            rolling_12m = unrate.rolling(252).min()  # ~12 months of trading days
            current = unrate.iloc[-1]
            low_12m = rolling_12m.iloc[-1]
            
            delta = current - low_12m
            
            if delta <= 0:
                return 0.0
            elif delta < 0.5:
                return 2.5
            elif delta < 1.0:
                return 5.0
            else:
                return 10.0
                
        except Exception as e:
            print(f"Warning: Error scoring unemployment trend: {e}")
            return 0.0
    
    def score_yield_curve(self) -> float:
        """
        Category 1.2: Yield Curve Signal (0-10 points)
        0 points: Never inverted recently
        5 points: Briefly inverted, now modestly positive
        10 points: Deep, long inversion followed by steepening
        """
        try:
            # Fetch 10Y-2Y spread
            t10y2y = self.fred.fetch_series('T10Y2Y', start_date='2020-01-01')
            
            if len(t10y2y) < 60:
                return 0.0
            
            # Check recent history (last 252 trading days ~1 year)
            recent = t10y2y.iloc[-252:] if len(t10y2y) >= 252 else t10y2y
            
            # Check if inverted recently
            was_inverted = (recent < 0).any()
            current_spread = t10y2y.iloc[-1]
            
            if not was_inverted:
                return 0.0
            
            # Check depth and duration of inversion
            inversion_periods = recent[recent < 0]
            if len(inversion_periods) > 0:
                max_inversion_depth = abs(inversion_periods.min())
                inversion_duration = len(inversion_periods)
                
                # Deep inversion (>1%) for long period (>60 days) = 10 points
                if max_inversion_depth > 1.0 and inversion_duration > 60:
                    # Check if now steepening (recently uninverted)
                    if current_spread > 0.5:
                        return 10.0
                    else:
                        return 8.0
                elif max_inversion_depth > 0.5:
                    return 5.0
            
            return 0.0
            
        except Exception as e:
            print(f"Warning: Error scoring yield curve: {e}")
            return 0.0
    
    def score_gdp_vs_stall(self) -> float:
        """
        Category 1.3: GDP vs Stall Speed (0-10 points)
        0 points: >2.5% trend growth
        5 points: 1.5-2.5% growth
        10 points: <1.5% or multiple weak/negative quarters
        """
        try:
            # Fetch GDP growth rate
            gdp_growth = self.fred.fetch_series('A191RL1Q225SBEA', start_date='2020-01-01')
            
            if len(gdp_growth) < 4:
                return 0.0
            
            # Calculate trailing 4-quarter average
            trailing_4q = gdp_growth.iloc[-4:].mean()
            
            if trailing_4q > 2.5:
                return 0.0
            elif trailing_4q > 1.5:
                return 5.0
            else:
                return 10.0
                
        except Exception as e:
            print(f"Warning: Error scoring GDP: {e}")
            # Default to moderate risk if can't fetch
            return 5.0
    
    def score_forward_pe(self) -> float:
        """
        Category 2.1: Forward P/E vs Historical (0-10 points)
        0 points: ≤ Historical median (~16x)
        5 points: 1 SD above (~19-20x)
        10 points: Dot-com/2021 levels (22x+)
        """
        try:
            forward_pe = self.yfinance.get_forward_pe('SPY')
            
            if forward_pe is None:
                # Fallback: try to calculate from price/earnings
                spy_info = self.yfinance.get_info('SPY')
                if 'trailingPE' in spy_info and spy_info['trailingPE']:
                    forward_pe = spy_info['trailingPE']
                else:
                    return 0.0
            
            if forward_pe <= 16:
                return 0.0
            elif forward_pe <= 20:
                return 5.0
            else:
                return 10.0
                
        except Exception as e:
            print(f"Warning: Error scoring forward P/E: {e}")
            return 0.0
    
    def score_buffett_indicator(self) -> float:
        """
        Category 2.2: Buffett Indicator (0-10 points)
        0 points: Normal range (<100%)
        5 points: High but below prior peaks (100-140%)
        10 points: At/above dot-com & 2007 highs (>140%)
        """
        try:
            # Market cap / GDP ratio
            # DDDM01USA156NWDB = Market capitalization of listed domestic companies (% of GDP)
            # This series directly provides the ratio we need
            buffett_ratio = self.fred.fetch_series('DDDM01USA156NWDB', start_date='2020-01-01')
            
            if len(buffett_ratio) == 0:
                return 0.0
            
            # Get latest value (already in percentage)
            ratio = buffett_ratio.iloc[-1]
            
            if ratio < 100:
                return 0.0
            elif ratio < 140:
                return 5.0
            else:
                return 10.0
                
        except Exception as e:
            print(f"Warning: Error scoring Buffett Indicator: {e}")
            return 0.0
    
    def score_equity_yield_vs_tbill(self) -> float:
        """
        Category 2.3: Equity Yield vs T-Bills (0-10 points)
        0 points: Earnings yield >> T-bill yield
        5 points: Roughly equal
        10 points: Equity yield < T-bill yield
        """
        try:
            # Get forward P/E to calculate earnings yield
            forward_pe = self.yfinance.get_forward_pe('SPY')
            if forward_pe is None or forward_pe <= 0:
                return 0.0
            
            earnings_yield = (1.0 / forward_pe) * 100  # Percentage
            
            # Get 3-month T-bill rate
            tbill_3m = self.fred.get_latest_value('DTB3')
            if tbill_3m is None:
                return 0.0
            
            spread = earnings_yield - tbill_3m
            
            if spread > 2.0:
                return 0.0
            elif spread > 0:
                return 5.0
            else:
                return 10.0
                
        except Exception as e:
            print(f"Warning: Error scoring equity yield: {e}")
            return 0.0
    
    def score_hedge_fund_leverage(self) -> float:
        """
        Category 3.1: Hedge Fund Leverage (0-10 points)
        Manual input from Fed Financial Stability Report
        """
        return float(self.manual_inputs.get('hedge_fund_leverage', 0))
    
    def score_corporate_credit(self) -> float:
        """
        Category 3.2: Corporate Credit Health (0-10 points)
        0 points: Tight spreads, strong coverage
        5 points: Mild deterioration
        10 points: Widespread distress
        """
        try:
            # Fetch HY spread
            hy_spread = self.fred.fetch_series('BAMLH0A0HYM2', start_date='2020-01-01')
            
            if len(hy_spread) == 0:
                return 0.0
            
            current_spread = hy_spread.iloc[-1]
            historical_median = hy_spread.median()
            
            # Normalize: <400bps = 0, 400-600 = 5, >600 = 10
            if current_spread < 400:
                return 0.0
            elif current_spread < 600:
                return 5.0
            else:
                return 10.0
                
        except Exception as e:
            print(f"Warning: Error scoring corporate credit: {e}")
            return 0.0
    
    def score_cre_stress(self) -> float:
        """
        Category 3.3: CRE / Regional Bank Stress (0-10 points)
        Manual input for now (would need FDIC data)
        """
        delinquency_rate = self.manual_inputs.get('cre_delinquency_rate', 0)
        
        if delinquency_rate < 2.0:
            return 0.0
        elif delinquency_rate < 5.0:
            return 5.0
        else:
            return 10.0
    
    def score_earnings_breadth(self) -> float:
        """
        Category 4: Earnings & Margins (0-10 points)
        Compare S&P 500 vs equal-weight performance
        """
        try:
            # Fetch SPY (cap-weighted) and RSP (equal-weight)
            spy = self.yfinance.fetch_ticker('SPY', period='1y')
            rsp = self.yfinance.fetch_ticker('RSP', period='1y')
            
            if len(spy) == 0 or len(rsp) == 0:
                return 0.0
            
            # Calculate 6-month returns
            spy_return = (spy['Close'].iloc[-1] / spy['Close'].iloc[-126] - 1) * 100 if len(spy) >= 126 else 0
            rsp_return = (rsp['Close'].iloc[-1] / rsp['Close'].iloc[-126] - 1) * 100 if len(rsp) >= 126 else 0
            
            # If equal-weight underperforming significantly, earnings are concentrated
            underperformance = spy_return - rsp_return
            
            if underperformance < -5:
                return 10.0  # Mega-cap dominated
            elif underperformance < 0:
                return 5.0
            else:
                return 0.0
                
        except Exception as e:
            print(f"Warning: Error scoring earnings breadth: {e}")
            return 0.0
    
    def score_sentiment(self) -> float:
        """
        Category 5: Sentiment & Liquidity (-10 to +10 points)
        Can reduce total risk if extreme fear + cash on sidelines
        """
        try:
            # Get VIX level
            vix_data = self.yfinance.fetch_ticker('^VIX', period='1y')
            if len(vix_data) == 0:
                return 0.0
            
            current_vix = vix_data['Close'].iloc[-1]
            
            # VIX > 30 = fear (reduces risk score)
            # VIX < 15 = complacency (adds to risk score)
            if current_vix > 30:
                return -5.0  # Extreme fear reduces risk
            elif current_vix < 15:
                return 5.0  # Complacency adds risk
            else:
                return 0.0
                
        except Exception as e:
            print(f"Warning: Error scoring sentiment: {e}")
            return 0.0
    
    def calculate_frs(self) -> Dict[str, Any]:
        """
        Calculate complete Fundamental Risk Score
        
        Returns:
            dict with FRS score, breakdown, correction probability, etc.
        """
        print("Calculating Fundamental Risk Score...")
        
        # Category 1: Macro/Cycle (0-30)
        unemployment_score = self.score_unemployment_trend()
        yield_curve_score = self.score_yield_curve()
        gdp_score = self.score_gdp_vs_stall()
        macro_score = min(30, unemployment_score + yield_curve_score + gdp_score)
        
        # Category 2: Valuation (0-25)
        pe_score = self.score_forward_pe()
        buffett_score = self.score_buffett_indicator()
        equity_yield_score = self.score_equity_yield_vs_tbill()
        valuation_raw = pe_score + buffett_score + equity_yield_score
        valuation_score = min(25, valuation_raw * 25 / 30)  # Scale to 25
        
        # Category 3: Leverage & Stability (0-25)
        hedge_fund_score = self.score_hedge_fund_leverage()
        corp_credit_score = self.score_corporate_credit()
        cre_score = self.score_cre_stress()
        leverage_raw = hedge_fund_score + corp_credit_score + cre_score
        leverage_score = min(25, leverage_raw * 25 / 30)  # Scale to 25
        
        # Category 4: Earnings (0-10)
        earnings_score = self.score_earnings_breadth()
        
        # Category 5: Sentiment (-10 to +10)
        sentiment_score = self.score_sentiment()
        
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
            "manual_inputs": self.manual_inputs,
            "component_details": {
                "unemployment": round(unemployment_score, 1),
                "yield_curve": round(yield_curve_score, 1),
                "gdp": round(gdp_score, 1),
                "forward_pe": round(pe_score, 1),
                "buffett_indicator": round(buffett_score, 1),
                "equity_yield": round(equity_yield_score, 1),
                "hedge_fund_leverage": round(hedge_fund_score, 1),
                "corporate_credit": round(corp_credit_score, 1),
                "cre_stress": round(cre_score, 1),
                "earnings_breadth": round(earnings_score, 1),
                "sentiment": round(sentiment_score, 1)
            }
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


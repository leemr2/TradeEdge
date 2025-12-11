"""
Category 5: Technical/Sentiment (0-10 points)
Identifies extremes in market sentiment and technical divergences
"""

from datetime import datetime
from typing import Dict, Any, Optional
from .base_category import BaseCategory, ComponentScore, CategoryMetadata


class SentimentCategory(BaseCategory):
    """Category 5: Technical/Sentiment Risk Assessment"""
    
    def calculate(self) -> Dict[str, Any]:
        """
        Calculate technical/sentiment category score
        Sum of two indicators (each 0-5 points), capped at 10
        """
        breadth_score = self._score_breadth_divergence()
        sentiment_score = self._score_sentiment_extremes()
        
        # Sum and cap at 10 points
        total_score = min(10.0, breadth_score['score'] + sentiment_score['score'])
        
        return {
            'score': round(total_score, 1),
            'max_points': 10.0,
            'components': {
                'breadth_divergence': breadth_score,
                'sentiment_extremes': sentiment_score,
            },
            'metadata': self.get_metadata(),
        }
    
    def _score_breadth_divergence(self) -> Dict[str, Any]:
        """
        Indicator 5.1: Breadth Divergence (0-5 points)
        
        Combines market position (SPY distance from 52-week high) with 
        volatility (VIX) to identify dangerous divergence patterns.
        
        Bad = near highs + low VIX (complacent)
        Good = off highs OR elevated VIX (cautious)
        """
        try:
            # Get SPY data (3-month window)
            spy_data = self.yfinance.fetch_ticker('SPY', period='3mo')
            if len(spy_data) == 0:
                return self._error_response('breadth_divergence', 'Insufficient SPY data')
            
            # Calculate distance from 52-week high
            current_spy = spy_data['Close'].iloc[-1]
            high_52w = spy_data['High'].max()
            pct_from_high = ((current_spy - high_52w) / high_52w) * 100
            
            # Get VIX (1-month window for current level)
            vix_data = self.yfinance.fetch_ticker('^VIX', period='1mo')
            if len(vix_data) == 0:
                return self._error_response('breadth_divergence', 'Insufficient VIX data')
            
            current_vix = vix_data['Close'].iloc[-1]
            last_updated = datetime.now().isoformat()
            
            # Score based on divergence pattern
            # Bad = near highs + low VIX (complacent)
            if pct_from_high > -2 and current_vix < 15:
                score = 5.0
                interpretation = f'Severe divergence: At highs ({pct_from_high:.1f}% from high) with low VIX ({current_vix:.1f}) - extreme complacency'
            elif pct_from_high > -5 or (15 <= current_vix < 20):
                score = 2.5
                interpretation = f'Moderate divergence: {pct_from_high:.1f}% from high, VIX {current_vix:.1f}'
            else:
                score = 0.0
                interpretation = f'No divergence: Off highs ({pct_from_high:.1f}%) or VIX elevated ({current_vix:.1f}) - healthy caution'
            
            return {
                'name': 'breadth_divergence',
                'score': round(score, 1),
                'value': {
                    'spy_pct_from_52w_high': round(pct_from_high, 2),
                    'current_vix': round(current_vix, 2)
                },
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'Yahoo Finance: SPY, ^VIX'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring breadth divergence: {e}")
            return self._error_response('breadth_divergence', str(e))
    
    def _score_sentiment_extremes(self) -> Dict[str, Any]:
        """
        Indicator 5.2: Sentiment Extremes (0-5 points)
        
        Uses VIX as contrarian indicator:
        - Low VIX = complacency = higher risk score (bad)
        - High VIX = fear = lower risk score (good)
        
        Scoring:
        - VIX <13: 5 points (extreme complacency)
        - VIX 13-15: 3-5 points (very low fear)
        - VIX 15-18: 2.5 points (low fear)
        - VIX 18-20: 1-2 points (neutral)
        - VIX >20: 0 points (fear present, healthy)
        """
        try:
            # Get VIX level
            vix_data = self.yfinance.fetch_ticker('^VIX', period='1mo')
            if len(vix_data) == 0:
                return self._error_response('sentiment_extremes', 'Insufficient VIX data')
            
            current_vix = vix_data['Close'].iloc[-1]
            last_updated = datetime.now().isoformat()
            
            # Score based on VIX level (contrarian)
            # Low VIX = complacency = higher risk score
            if current_vix > 20:
                score = 0.0
                interpretation = f'Fear present (VIX {current_vix:.1f}) - healthy caution, no complacency risk'
            elif 18 <= current_vix <= 20:
                # Linear interpolation 0-2
                score = (20 - current_vix) / 2
                interpretation = f'Neutral sentiment (VIX {current_vix:.1f}) - slight complacency'
            elif 15 <= current_vix < 18:
                score = 2.5
                interpretation = f'Low fear (VIX {current_vix:.1f}) - getting complacent'
            elif 13 <= current_vix < 15:
                # Linear interpolation 2.5-5
                score = 2.5 + ((15 - current_vix) / 2) * 2.5
                interpretation = f'Very low fear (VIX {current_vix:.1f}) - complacent market'
            else:  # current_vix < 13
                score = 5.0
                interpretation = f'Extreme complacency (VIX {current_vix:.1f}) - maximum contrarian risk signal'
            
            return {
                'name': 'sentiment_extremes',
                'score': round(score, 1),
                'value': round(current_vix, 2),
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'Yahoo Finance: ^VIX',
                'historical_context': 'VIX historical average ~19; <13 = extreme complacency, >30 = extreme fear'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring sentiment extremes: {e}")
            return self._error_response('sentiment_extremes', str(e))
    
    def _error_response(self, indicator_name: str, error_msg: str) -> Dict[str, Any]:
        """Generate error response for an indicator"""
        return {
            'name': indicator_name,
            'score': 0.0,
            'value': None,
            'last_updated': None,
            'interpretation': f'Error: {error_msg}',
            'data_source': 'Yahoo Finance'
        }
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        return CategoryMetadata(
            name='Technical/Sentiment',
            max_points=10.0,
            description='Identifies extremes in market sentiment and technical divergences through breadth analysis (SPY vs highs) and VIX-based sentiment measures. Low VIX + near highs = dangerous complacency.',
            update_frequency='Real-time (during market hours)',
            data_sources=['Yahoo Finance: SPY, ^VIX'],
            next_update='Daily (after market close)'
        )


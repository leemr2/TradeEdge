"""
Category 5: Sentiment (-10 to +10 points)
Identifies extremes in market sentiment and technical divergences
"""

from datetime import datetime
from typing import Dict, Any, Optional
from .base_category import BaseCategory, ComponentScore, CategoryMetadata


class SentimentCategory(BaseCategory):
    """Category 5: Sentiment Risk Assessment"""
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate sentiment category score"""
        sentiment_score = self._score_sentiment()
        
        return {
            'score': round(sentiment_score['score'], 1),
            'max_points': 10.0,
            'min_points': -10.0,
            'components': {
                'sentiment': sentiment_score,
            },
            'metadata': self.get_metadata(),
        }
    
    def _score_sentiment(self) -> Dict[str, Any]:
        """
        Category 5: Sentiment & Liquidity (-10 to +10 points)
        Can reduce total risk if extreme fear + cash on sidelines
        """
        try:
            # Get VIX level
            vix_data = self.yfinance.fetch_ticker('^VIX', period='1y')
            if len(vix_data) == 0:
                return {
                    'name': 'sentiment',
                    'score': 0.0,
                    'value': None,
                    'last_updated': None,
                    'interpretation': 'Insufficient data',
                    'data_source': 'Yahoo Finance: ^VIX'
                }
            
            current_vix = vix_data['Close'].iloc[-1]
            last_updated = datetime.now().isoformat()
            
            # VIX > 30 = fear (reduces risk score)
            # VIX < 15 = complacency (adds to risk score)
            if current_vix > 30:
                score = -5.0
                interpretation = 'Extreme fear present - reduces risk score (contrarian indicator)'
            elif current_vix < 15:
                score = 5.0
                interpretation = 'Low fear/complacency - adds to risk score (contrarian indicator)'
            else:
                score = 0.0
                interpretation = 'Moderate fear levels - neutral'
            
            return {
                'name': 'sentiment',
                'score': round(score, 1),
                'value': round(current_vix, 2),
                'last_updated': last_updated,
                'interpretation': interpretation,
                'data_source': 'Yahoo Finance: ^VIX'
            }
                
        except Exception as e:
            print(f"Warning: Error scoring sentiment: {e}")
            return {
                'name': 'sentiment',
                'score': 0.0,
                'value': None,
                'last_updated': None,
                'interpretation': f'Error: {str(e)}',
                'data_source': 'Yahoo Finance: ^VIX'
            }
    
    def get_metadata(self) -> CategoryMetadata:
        """Get category metadata"""
        return CategoryMetadata(
            name='Sentiment',
            max_points=10.0,
            description='Identifies extremes in market sentiment through VIX levels. Low VIX indicates complacency (adds risk), high VIX indicates fear (reduces risk).',
            update_frequency='Real-time (during market hours)',
            data_sources=['Yahoo Finance: ^VIX'],
            next_update='Daily (after market close)'
        )


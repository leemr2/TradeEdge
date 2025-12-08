"""
FastAPI Backend for TradeEdge
HTTP wrapper around Python analytics modules
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import lru_cache

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass  # python-dotenv not installed, use system env vars only

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.core.volatility_predictor import VolatilityPredictorV2
from analytics.core.frs_calculator import FRSCalculator
from analytics.core.cmds_calculator import CMDSCalculator


app = FastAPI(
    title="TradeEdge API",
    description="AI-Powered Investment Command Center API",
    version="1.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache for responses (in-memory, 5-15 min TTL)
response_cache: Dict[str, tuple] = {}  # {endpoint: (data, expiry_time)}


def get_cached_response(endpoint: str, ttl_minutes: int = 5) -> Optional[Dict[str, Any]]:
    """Get cached response if still valid"""
    if endpoint in response_cache:
        data, expiry = response_cache[endpoint]
        if datetime.now() < expiry:
            return data
        else:
            del response_cache[endpoint]
    return None


def set_cached_response(endpoint: str, data: Dict[str, Any], ttl_minutes: int = 5):
    """Cache response with TTL"""
    expiry = datetime.now() + timedelta(minutes=ttl_minutes)
    response_cache[endpoint] = (data, expiry)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "TradeEdge API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "volatility": "/api/volatility",
            "frs": "/api/frs",
            "cmds": "/api/cmds"
        }
    }


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/volatility")
async def get_volatility():
    """
    Get Volatility Predictor (VP) score
    
    Returns:
        JSON with VP score, confidence, spike probability, etc.
    """
    # Check cache
    cached = get_cached_response("volatility", ttl_minutes=15)
    if cached:
        return JSONResponse(cached)
    
    try:
        predictor = VolatilityPredictorV2()
        
        # Try to load model
        if not predictor.load_model():
            raise HTTPException(
                status_code=503,
                detail="VP model not trained. Train model first with --mode train"
            )
        
        # Ensure we have features
        if predictor.features is None or len(predictor.features) == 0:
            predictor.prepare_training_data()
        
        result = predictor.get_current_prediction()
        
        # Cache response
        set_cached_response("volatility", result, ttl_minutes=15)
        
        return JSONResponse(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating VP: {str(e)}")


@app.get("/api/frs")
async def get_frs():
    """
    Get Fundamental Risk Score (FRS)
    
    Returns:
        JSON with FRS score, breakdown, correction probability, etc.
    """
    # Check cache
    cached = get_cached_response("frs", ttl_minutes=60)  # Cache for 1 hour
    if cached:
        return JSONResponse(cached)
    
    try:
        fred_api_key = os.getenv('FRED_API_KEY')
        calculator = FRSCalculator(fred_api_key=fred_api_key)
        
        result = calculator.calculate_frs()
        
        # Cache response
        set_cached_response("frs", result, ttl_minutes=60)
        
        return JSONResponse(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating FRS: {str(e)}")


@app.get("/api/cmds")
async def get_cmds(frs_weight: Optional[float] = 0.65, vp_weight: Optional[float] = 0.35):
    """
    Get Combined Market Danger Score (CMDS)
    
    Args:
        frs_weight: Weight for FRS (default 0.65)
        vp_weight: Weight for VP (default 0.35)
    
    Returns:
        JSON with CMDS score, zone, allocation recommendations, etc.
    """
    # Validate weights
    if abs(frs_weight + vp_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail="FRS and VP weights must sum to 1.0"
        )
    
    # Check cache (cache key includes weights)
    cache_key = f"cmds_{frs_weight}_{vp_weight}"
    cached = get_cached_response(cache_key, ttl_minutes=5)
    if cached:
        return JSONResponse(cached)
    
    try:
        fred_api_key = os.getenv('FRED_API_KEY')
        calculator = CMDSCalculator(
            frs_weight=frs_weight,
            vp_weight=vp_weight,
            fred_api_key=fred_api_key
        )
        
        result = calculator.calculate_cmds()
        
        # Cache response
        set_cached_response(cache_key, result, ttl_minutes=5)
        
        return JSONResponse(result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating CMDS: {str(e)}")


@app.get("/api/cmds/history")
async def get_cmds_history(days: int = 30):
    """
    Get historical CMDS scores (placeholder for future implementation)
    
    Args:
        days: Number of days of history to return
    
    Returns:
        JSON array of historical CMDS scores
    """
    # TODO: Implement historical data storage and retrieval
    return {
        "message": "Historical data not yet implemented",
        "days_requested": days
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


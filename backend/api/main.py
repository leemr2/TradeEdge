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
import math
import json

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
from analytics.core.manual_inputs import (
    update_manual_input, 
    load_manual_inputs,
    save_manual_inputs,
    get_field_metadata,
    get_category_groups
)


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize an object for JSON serialization
    Converts NaN and Inf to None, handles nested dicts/lists
    """
    if obj is None:
        return None
    
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    
    if isinstance(obj, (int, str, bool)):
        return obj
    
    # For datetime and other objects, try to convert to string
    if isinstance(obj, datetime):
        return obj.isoformat()
    
    try:
        # Try to convert to string as fallback
        return str(obj)
    except:
        return None


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
        return JSONResponse(sanitize_for_json(cached))
    
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
        
        # Sanitize before caching and returning
        result = sanitize_for_json(result)
        
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
        return JSONResponse(sanitize_for_json(cached))
    
    try:
        fred_api_key = os.getenv('FRED_API_KEY')
        calculator = FRSCalculator(fred_api_key=fred_api_key)
        
        result = calculator.calculate_frs()
        
        # Sanitize before caching and returning
        result = sanitize_for_json(result)
        
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
        return JSONResponse(sanitize_for_json(cached))
    
    try:
        fred_api_key = os.getenv('FRED_API_KEY')
        calculator = CMDSCalculator(
            frs_weight=frs_weight,
            vp_weight=vp_weight,
            fred_api_key=fred_api_key
        )
        
        result = calculator.calculate_cmds()
        
        # Sanitize before caching and returning
        result = sanitize_for_json(result)
        
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


class ManualInputUpdate(BaseModel):
    """Model for batch updating manual inputs - accepts any field dynamically"""
    class Config:
        extra = 'allow'  # Allow any fields


@app.post("/api/frs/manual-inputs")
async def update_frs_manual_inputs(updates: Dict[str, Any]):
    """
    Update manual input values for FRS calculation
    
    Accepts any manual input field dynamically with validation based on field metadata
    
    Args:
        updates: Dictionary with field names and values to update
    
    Returns:
        Updated manual inputs dictionary
    """
    try:
        if not updates:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided"
            )
        
        # Load current inputs and metadata
        current_inputs = load_manual_inputs()
        metadata = get_field_metadata()
        
        # Validate and update each field
        updated_fields = []
        for key, value in updates.items():
            # Skip _as_of fields - they'll be handled separately
            if key.endswith('_as_of') or key in ['last_full_update', 'version']:
                current_inputs[key] = value
                continue
            
            # Validate field exists in metadata
            if key not in metadata and key not in ['as_of']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown field: {key}"
                )
            
            # Validate value range if metadata available
            if key in metadata:
                field_meta = metadata[key]
                if 'min' in field_meta and 'max' in field_meta:
                    if not (field_meta['min'] <= value <= field_meta['max']):
                        raise HTTPException(
                            status_code=400,
                            detail=f"{key} must be between {field_meta['min']} and {field_meta['max']}"
                        )
            
            # Update the field
            current_inputs[key] = value
            updated_fields.append(key)
            
            # Update as_of date for this field if provided
            as_of_key = f'{key}_as_of'
            if 'as_of' in updates:
                current_inputs[as_of_key] = updates['as_of']
            elif as_of_key not in current_inputs:
                current_inputs[as_of_key] = datetime.now().isoformat()
        
        # Update timestamp
        current_inputs['last_full_update'] = datetime.now().isoformat()
        
        # Save all changes
        save_manual_inputs(current_inputs)
        
        # Clear all caches since inputs changed
        response_cache.clear()
        
        return {
            "status": "success",
            "updated_fields": updated_fields,
            "values": current_inputs,
            "message": f"Successfully updated {len(updated_fields)} field(s)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating manual inputs: {str(e)}")


@app.get("/api/frs/manual-inputs")
async def get_frs_manual_inputs():
    """
    Get all current manual input values with metadata
    
    Returns:
        Dictionary with current manual input values and complete metadata
    """
    try:
        inputs = load_manual_inputs()
        metadata = get_field_metadata()
        category_groups = get_category_groups()
        
        # Format response with enhanced structure
        response = {
            'values': inputs,
            'metadata': metadata,
            'categories': category_groups,
            'last_updated': inputs.get('last_full_update'),
            'version': inputs.get('version', '1.0')
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading manual inputs: {str(e)}")


@app.get("/api/frs/manual-inputs/metadata")
async def get_manual_inputs_metadata():
    """
    Get comprehensive metadata for all manual input fields
    
    Returns:
        Field metadata including descriptions, ranges, instructions, data sources
    """
    try:
        metadata = get_field_metadata()
        categories = get_category_groups()
        
        return {
            'fields': metadata,
            'categories': categories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading metadata: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


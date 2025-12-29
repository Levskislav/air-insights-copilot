"""
service/routes.py
=================
HTTP endpoint definitions (routes).

This file defines the actual API endpoints that clients call.
The "thin controller" pattern: routes only handle HTTP concerns,
all business logic is delegated to the agent/orchestrator.

Endpoints:
- POST /analyze    → Air quality + weather + snow analysis with AI guidance
- POST /geocode    → Convert place name to coordinates
- GET  /apod/today → NASA Astronomy Picture of the Day (optional)
"""

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from agent.config import config, MAX_FORECAST_HOURS
from agent.logging_config import log_error
from agent.exceptions import AirInsightsError, GeocodingError, ConfigurationError
from agent.orchestrator import analyze_air_and_weather, apod_today
from agent.tools.google_geocoding import geocode_place
from service.schemas import (
    AnalyzeRequest, AnalyzeResponse, 
    ApodResponse,
    GeocodeRequest, GeocodeResponse
)

# Rate limiter instance - shared with main.py via app.state
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{config.rate_limit_per_minute}/minute"])

# =============================================================================
# CREATE THE ROUTER
# =============================================================================

# APIRouter groups related endpoints together
# prefix="" means endpoints are at root level (/analyze, not /api/analyze)
router = APIRouter()


# =============================================================================
# MAIN ENDPOINT: POST /analyze
# =============================================================================

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,  # FastAPI validates output matches this schema
    tags=["Analysis"],               # Groups this endpoint in Swagger UI
    summary="Analyze air quality and weather",
    description="""
    Fetches air quality (PM2.5, PM10), temperature, and snow data for a location,
    then generates AI-powered guidance for outdoor activities.
    
    **Features:**
    - Accepts coordinates OR place name (auto-geocoded)
    - Data from Open-Meteo (free, no API key needed)
    - Snow data included (snowfall, snow depth)
    - AI guidance generated via GitHub Models LLM
    - Results cached for 10 minutes
    
    **Rate limit:** 30 requests per minute
    
    **Example with coordinates:**
    ```json
    {
        "latitude": 42.6977,
        "longitude": 23.3219,
        "hours": 6
    }
    ```
    
    **Example with place name:**
    ```json
    {
        "place_name": "Vitosha",
        "hours": 6
    }
    ```
    """
)
@limiter.limit("30/minute")
async def analyze(request: Request, body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Main analysis endpoint.
    
    Flow:
    1. Validate input (handled automatically by Pydantic)
    2. Geocode place name if provided (instead of coordinates)
    3. Call orchestrator to fetch data and generate guidance
    4. Return structured response
    
    Args:
        request: AnalyzeRequest with (latitude, longitude) OR place_name, and hours
        
    Returns:
        AnalyzeResponse with pm25_avg, pm10_avg, temp_avg, snow data, and guidance_text
        
    Raises:
        HTTPException: If something goes wrong during processing
    """
    try:
        # Explicit hours validation with user-friendly message
        if body.hours > MAX_FORECAST_HOURS:
            return AnalyzeResponse(
                pm25_avg=None,
                pm10_avg=None,
                temp_avg=None,
                snowfall_sum=None,
                snow_depth_avg=None,
                guidance_text=f"Sorry, I can only provide weather forecasts up to {MAX_FORECAST_HOURS} hours ahead. You requested {body.hours} hours. Please try a shorter time period."
            )
        
        # Delegate to the orchestrator (agent layer)
        # The orchestrator handles: geocode → cache check → fetch data → validate → compute → LLM
        result = await analyze_air_and_weather(
            lat=body.latitude,
            lon=body.longitude,
            place_name=body.place_name,
            hours=body.hours
        )
        return result
        
    except AirInsightsError as e:
        # Our custom exceptions - preserve status code and message
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except ValueError as e:
        # Validation errors
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Unexpected errors - log and return generic message
        log_error(f"Error in /analyze", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


# =============================================================================
# OPTIONAL ENDPOINT: GET /apod/today
# =============================================================================

@router.get(
    "/apod/today",
    response_model=ApodResponse,
    tags=["NASA"],
    summary="Get NASA Astronomy Picture of the Day",
    description="""
    Fetches today's Astronomy Picture of the Day from NASA.
    
    This is a bonus feature that demonstrates calling external APIs.
    Uses NASA's free APOD API (DEMO_KEY or your own API key).
    
    **Rate limit:** 30 requests per minute
    """
)
@limiter.limit("30/minute")
async def get_apod_today(request: Request) -> ApodResponse:
    """
    Fetch NASA's Astronomy Picture of the Day.
    
    Returns:
        ApodResponse with title, url, and explanation
        
    Raises:
        HTTPException: If NASA API call fails
    """
    try:
        # Delegate to the orchestrator
        result = await apod_today()
        return result
        
    except AirInsightsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except Exception as e:
        log_error(f"Error in /apod/today", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch APOD")


# =============================================================================
# GEOCODING ENDPOINT: POST /geocode
# =============================================================================

@router.post(
    "/geocode",
    response_model=GeocodeResponse,
    tags=["Geocoding"],
    summary="Convert place name to coordinates",
    description="""
    Converts a place name (like "Sofia" or "Vitosha") to geographic coordinates.
    
    Uses Google Maps Geocoding API.
    
    **Rate limit:** 60 requests per minute
    
    **Example request:**
    ```json
    {
        "place_name": "Sofia"
    }
    ```
    
    **Example response:**
    ```json
    {
        "latitude": 42.6977,
        "longitude": 23.3219,
        "formatted_address": "Sofia, Bulgaria",
        "found": true
    }
    ```
    """
)
@limiter.limit("60/minute")
async def geocode(request: Request, body: GeocodeRequest) -> GeocodeResponse:
    """
    Geocode a place name to coordinates.
    
    Args:
        request: GeocodeRequest with place_name
        
    Returns:
        GeocodeResponse with latitude, longitude, formatted_address, found
        
    Raises:
        HTTPException: If geocoding service fails
    """
    try:
        result = await geocode_place(body.place_name)
        return result
        
    except ConfigurationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except AirInsightsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
        
    except Exception as e:
        log_error(f"Error in /geocode", error=str(e))
        raise HTTPException(status_code=500, detail="Geocoding service unavailable")
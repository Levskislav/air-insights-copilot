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

from fastapi import APIRouter, HTTPException

# Import our Pydantic models for request/response validation
from service.schemas import (
    AnalyzeRequest, AnalyzeResponse, 
    ApodResponse,
    GeocodeRequest, GeocodeResponse,
    RouteWeatherRequest, RouteWeatherResponse
)

# Import the agent orchestrator (business logic)
from agent.orchestrator import analyze_air_and_weather, apod_today, analyze_route_weather

# Import geocoding tool
from agent.tools.google_geocoding import geocode_place

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
        "place_name": "Витоша",
        "hours": 6
    }
    ```
    """
)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
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
        if request.hours > 72:
            return AnalyzeResponse(
                pm25_avg=None,
                pm10_avg=None,
                temp_avg=None,
                snowfall_sum=None,
                snow_depth_avg=None,
                guidance_text=f"Sorry, I can only provide weather forecasts up to 72 hours ahead. You requested {request.hours} hours. Please ask for a shorter time period (up to 3 days)."
            )
        
        # Delegate to the orchestrator (agent layer)
        # The orchestrator handles: geocode → cache check → fetch data → validate → compute → LLM
        result = await analyze_air_and_weather(
            lat=request.latitude,
            lon=request.longitude,
            place_name=request.place_name,
            hours=request.hours
        )
        return result
        
    except ValueError as e:
        # Validation errors (e.g., invalid coordinates)
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Unexpected errors - log and return generic message
        # In production, you'd log this properly
        print(f"Error in /analyze: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request"
        )


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
    """
)
async def get_apod_today() -> ApodResponse:
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
        
    except Exception as e:
        print(f"Error in /apod/today: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch APOD from NASA"
        )


# =============================================================================
# GEOCODING ENDPOINT: POST /geocode
# =============================================================================

@router.post(
    "/geocode",
    response_model=GeocodeResponse,
    tags=["Geocoding"],
    summary="Convert place name to coordinates",
    description="""
    Converts a place name (like "София" or "Vitosha") to geographic coordinates.
    
    Uses Google Maps Geocoding API.
    
    **Example request:**
    ```json
    {
        "place_name": "София"
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
async def geocode(request: GeocodeRequest) -> GeocodeResponse:
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
        # Call the geocoding tool
        result = await geocode_place(request.place_name)
        return result
        
    except ValueError as e:
        # Configuration error (no API key)
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        print(f"Error in /geocode: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to geocode place name"
        )


# =============================================================================
# ROUTE WEATHER ENDPOINT: POST /route-weather
# =============================================================================

@router.post(
    "/route-weather",
    response_model=RouteWeatherResponse,
    tags=["Route"],
    summary="Get weather along a driving route",
    description="""
    Gets weather forecast at multiple waypoints along a driving route.
    
    Perfect for planning road trips! Shows:
    - Temperature at each waypoint
    - Air quality (PM2.5)
    - Snow conditions
    - Weather warnings
    
    **Example request:**
    ```json
    {
        "origin": "София",
        "destination": "Пловдив",
        "departure_hours_from_now": 0
    }
    ```
    
    **Response includes:**
    - Route distance and duration
    - Weather at 5 waypoints along the route
    - AI-generated summary
    - Warnings (ice, snow, air quality)
    """
)
async def route_weather(request: RouteWeatherRequest) -> RouteWeatherResponse:
    """
    Get weather forecast along a driving route.
    
    Args:
        request: RouteWeatherRequest with origin, destination, and departure time
        
    Returns:
        RouteWeatherResponse with waypoints, summary, and warnings
        
    Raises:
        HTTPException: If route not found or service fails
    """
    try:
        result = await analyze_route_weather(
            origin=request.origin,
            destination=request.destination,
            departure_hours=request.departure_hours_from_now
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        print(f"Error in /route-weather: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get route weather"
        )
"""
service/routes.py
=================
HTTP endpoint definitions (routes).

This file defines the actual API endpoints that clients call.
The "thin controller" pattern: routes only handle HTTP concerns,
all business logic is delegated to the agent/orchestrator.

Endpoints:
- POST /analyze    → Air quality + weather analysis with AI guidance
- GET  /apod/today → NASA Astronomy Picture of the Day (optional)
"""

from fastapi import APIRouter, HTTPException

# Import our Pydantic models for request/response validation
from service.schemas import AnalyzeRequest, AnalyzeResponse, ApodResponse

# Import the agent orchestrator (business logic)
# Note: We'll implement this later, for now we'll use a stub
from agent.orchestrator import analyze_air_and_weather, apod_today

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
    Fetches air quality (PM2.5, PM10) and temperature data for a location,
    then generates AI-powered guidance for outdoor activities.
    
    **Features:**
    - Data from Open-Meteo (free, no API key needed)
    - Averages calculated for the specified time window
    - AI guidance generated via GitHub Models LLM
    - Results cached for 10 minutes
    
    **Example request:**
    {
        "latitude": 42.6977,
        "longitude": 23.3219,
        "hours": 6
    }
        """
)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Main analysis endpoint.
    
    Flow:
    1. Validate input (handled automatically by Pydantic)
    2. Call orchestrator to fetch data and generate guidance
    3. Return structured response
    
    Args:
        request: AnalyzeRequest with latitude, longitude, and hours
        
    Returns:
        AnalyzeResponse with pm25_avg, pm10_avg, temp_avg, and guidance_text
        
    Raises:
        HTTPException: If something goes wrong during processing
    """
    try:
        # Delegate to the orchestrator (agent layer)
        # The orchestrator handles: cache check → fetch data → validate → compute → LLM
        result = await analyze_air_and_weather(
            lat=request.latitude,
            lon=request.longitude,
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
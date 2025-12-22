"""
service/schemas.py
==================
Pydantic models for request/response validation.

These models define the "contract" of our API:
- What data the client must send (request)
- What data the server returns (response)

FastAPI uses these models to:
1. Validate incoming JSON automatically
2. Generate OpenAPI/Swagger documentation
3. Provide type hints for IDE autocompletion
"""

from pydantic import BaseModel, Field


# =============================================================================
# REQUEST MODELS (what the client sends to us)
# =============================================================================

class AnalyzeRequest(BaseModel):
    """
    Request body for POST /analyze endpoint.
    
    The client sends coordinates (latitude, longitude) and a time window (hours)
    to get air quality and weather analysis.
    
    Example:
        {
            "latitude": 42.6977,
            "longitude": 23.3219,
            "hours": 6
        }
    """
    
    # Latitude: geographic coordinate (-90 to +90)
    # Sofia, Bulgaria is around 42.7
    latitude: float = Field(
        ...,  # ... means required (no default value)
        description="Latitude coordinate (-90 to 90)",
        ge=-90,  # ge = greater than or equal
        le=90    # le = less than or equal
    )
    
    # Longitude: geographic coordinate (-180 to +180)
    # Sofia, Bulgaria is around 23.3
    longitude: float = Field(
        ...,
        description="Longitude coordinate (-180 to 180)",
        ge=-180,
        le=180
    )
    
    # Hours: how many hours ahead to analyze (1 to 168)
    # Open-Meteo provides up to 7 days forecast = 168 hours
    # Default is 6 hours for typical outdoor activity planning
    hours: int = Field(
        default=6,  # Default to 6 hours if not specified
        description="Number of hours to analyze (1-168)",
        ge=1,    # Minimum 1 hour
        le=168   # Maximum 168 hours (7 days)
    )


# =============================================================================
# RESPONSE MODELS (what we send back to the client)
# =============================================================================

class AnalyzeResponse(BaseModel):
    """
    Response body for POST /analyze endpoint.
    
    Contains averaged air quality metrics, temperature, and AI-generated guidance.
    
    Example:
        {
            "pm25_avg": 12.5,
            "pm10_avg": 18.3,
            "temp_avg": 15.2,
            "guidance_text": "Air quality is moderate..."
        }
    """
    
    # PM2.5 average (fine particulate matter, μg/m³)
    # Can be None if data is unavailable
    # WHO guideline: < 15 μg/m³ annual mean
    pm25_avg: float | None = Field(
        default=None,
        description="Average PM2.5 concentration (μg/m³) for the requested hours"
    )
    
    # PM10 average (coarse particulate matter, μg/m³)
    # Can be None if data is unavailable
    # WHO guideline: < 45 μg/m³ annual mean
    pm10_avg: float | None = Field(
        default=None,
        description="Average PM10 concentration (μg/m³) for the requested hours"
    )
    
    # Temperature average (Celsius, at 2 meters above ground)
    # Can be None if data is unavailable
    temp_avg: float | None = Field(
        default=None,
        description="Average temperature (°C) at 2m height for the requested hours"
    )
    
    # AI-generated guidance text
    # Contains actionable advice based on the data
    # Always includes attribution: "Weather data by Open-Meteo.com"
    guidance_text: str = Field(
        ...,
        description="AI-generated guidance for outdoor activities"
    )


class ApodResponse(BaseModel):
    """
    Response body for GET /apod/today endpoint.
    
    Returns NASA's Astronomy Picture of the Day.
    This is an optional/bonus feature.
    
    Example:
        {
            "title": "The Andromeda Galaxy",
            "url": "https://apod.nasa.gov/apod/image/...",
            "explanation": "The Andromeda Galaxy is..."
        }
    """
    
    # Title of today's astronomy picture
    title: str = Field(
        ...,
        description="Title of the Astronomy Picture of the Day"
    )
    
    # URL to the image (or video)
    url: str = Field(
        ...,
        description="URL to the image or video"
    )
    
    # Explanation/description of the picture
    explanation: str = Field(
        ...,
        description="Scientific explanation of the picture"
    )
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

from pydantic import BaseModel, Field, model_validator


# =============================================================================
# REQUEST MODELS (what the client sends to us)
# =============================================================================

class AnalyzeRequest(BaseModel):
    """
    Request body for POST /analyze endpoint.
    
    The client can provide EITHER:
    - Coordinates (latitude, longitude)
    - OR a place name (which will be geocoded automatically)
    
    Example with coordinates:
        {
            "latitude": 42.6977,
            "longitude": 23.3219,
            "hours": 6
        }
        
    Example with place name:
        {
            "place_name": "Vitosha",
            "hours": 6
        }
    """
    
    # Option 1: Direct coordinates
    # Latitude: geographic coordinate (-90 to +90)
    latitude: float | None = Field(
        default=None,
        description="Latitude coordinate (-90 to 90). Optional if place_name provided.",
        ge=-90,
        le=90
    )
    
    # Longitude: geographic coordinate (-180 to +180)
    longitude: float | None = Field(
        default=None,
        description="Longitude coordinate (-180 to 180). Optional if place_name provided.",
        ge=-180,
        le=180
    )
    
    # Option 2: Place name (will be geocoded)
    place_name: str | None = Field(
        default=None,
        description="Place name to geocode (e.g., 'Sofia', 'Vitosha'). Optional if coordinates provided.",
        min_length=1,
        max_length=200
    )
    
    # Hours: how many hours ahead to analyze (1 to 72, validated in route)
    hours: int = Field(
        default=1,
        description="Number of hours to forecast ahead (1-72). Use 1 for current weather.",
        ge=1
    )
    
    @model_validator(mode='after')
    def check_location_provided(self):
        """Validate that either coordinates or place_name is provided."""
        has_coords = self.latitude is not None and self.longitude is not None
        has_place = self.place_name is not None
        
        if not has_coords and not has_place:
            raise ValueError(
                "Please provide either coordinates (latitude, longitude) "
                "or a place_name"
            )
        
        return self


# =============================================================================
# RESPONSE MODELS (what we send back to the client)
# =============================================================================

class AnalyzeResponse(BaseModel):
    """
    Response body for POST /analyze endpoint.
    
    Contains averaged air quality metrics, temperature, snow data, and AI-generated guidance.
    
    Example:
        {
            "pm25_avg": 12.5,
            "pm10_avg": 18.3,
            "temp_avg": 15.2,
            "snowfall_sum": 2.5,
            "snow_depth_avg": 10.0,
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
    
    # Snowfall sum (total snowfall in cm for the requested hours)
    # Can be None if data is unavailable
    snowfall_sum: float | None = Field(
        default=None,
        description="Total snowfall (cm) for the requested hours"
    )
    
    # Snow depth average (average snow on ground in cm)
    # Can be None if data is unavailable
    snow_depth_avg: float | None = Field(
        default=None,
        description="Average snow depth (cm) on the ground"
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


# =============================================================================
# GEOCODING MODELS
# =============================================================================

class GeocodeRequest(BaseModel):
    """
    Request body for POST /geocode endpoint.
    
    Converts a place name to geographic coordinates.
    
    Example:
        {
            "place_name": "Sofia"
        }
    """
    
    place_name: str = Field(
        ...,
        description="Place name to geocode (e.g., 'Sofia', 'Vitosha', 'Plovdiv, Bulgaria')",
        min_length=1,
        max_length=200
    )


class GeocodeResponse(BaseModel):
    """
    Response body for POST /geocode endpoint.
    
    Returns geographic coordinates for a place name.
    
    Example (success):
        {
            "latitude": 42.6977,
            "longitude": 23.3219,
            "formatted_address": "Sofia, Bulgaria",
            "found": true
        }
        
    Example (not found):
        {
            "latitude": null,
            "longitude": null,
            "formatted_address": null,
            "found": false,
            "error": "ZERO_RESULTS"
        }
    """
    
    latitude: float | None = Field(
        default=None,
        description="Latitude coordinate of the place"
    )
    
    longitude: float | None = Field(
        default=None,
        description="Longitude coordinate of the place"
    )
    
    formatted_address: str | None = Field(
        default=None,
        description="Full formatted address returned by Google"
    )
    
    found: bool = Field(
        ...,
        description="Whether the place was found"
    )
    
    error: str | None = Field(
        default=None,
        description="Error message if place was not found"
    )
"""
agent/tools/google_geocoding.py
===============================
Google Maps Geocoding API integration.

Converts place names (like "Sofia" or "Vitosha") to coordinates.

API Endpoint: https://maps.googleapis.com/maps/api/geocode/json
Authentication: Google Maps API Key

Pricing: $5 per 1000 requests (but $200 free credit/month)
"""

import os
from typing import Any

from agent.retry import request_with_retry
from agent.logging_config import log_debug, log_warning
from agent.exceptions import GeocodingError, ConfigurationError
from agent.config import DEFAULT_HTTP_TIMEOUT_SECONDS

# =============================================================================
# CONFIGURATION
# =============================================================================

# Google Geocoding API endpoint
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def geocode_place(place_name: str, language: str = "en") -> dict[str, Any]:
    """
    Convert a place name to geographic coordinates using Google Geocoding API.
    
    Args:
        place_name: The place to geocode (e.g., "Sofia", "Vitosha", "Plovdiv, Bulgaria")
        language: Response language code (default "bg" for Bulgarian)
        
    Returns:
        Dictionary with geocoding result:
        {
            "latitude": 42.6977,
            "longitude": 23.3219,
            "formatted_address": "Sofia, Bulgaria",
            "found": True
        }
        
        Or if not found:
        {
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "found": False,
            "error": "ZERO_RESULTS"
        }
        
    Raises:
        ValueError: If GOOGLE_MAPS_API_KEY is not configured
        
    Example:
        >>> result = await geocode_place("Sofia")
        >>> print(result)
        {
            "latitude": 42.6977,
            "longitude": 23.3219,
            "formatted_address": "Sofia, Bulgaria",
            "found": True
        }
    """
    
    # Get API key from environment (support both old and new names)
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key or api_key == "replace_me":
        raise ConfigurationError("GOOGLE_MAPS_API_KEY")
    
    log_debug(f"Geocoding lookup", place=place_name)
    
    # Build query parameters
    params = {
        "address": place_name,
        "key": api_key,
        "language": language  # Response language
    }
    
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", str(DEFAULT_HTTP_TIMEOUT_SECONDS)))
    
    # Make the API call (may throw ExternalAPIError if circuit breaker open)
    response = await request_with_retry(
        method="GET",
        url=GEOCODE_URL,
        params=params,
        timeout=timeout
    )
    
    # Check API status
    status = response.get("status", "UNKNOWN_ERROR")
    
    # Handle Google-specific error statuses
    if status == "REQUEST_DENIED":
        raise ConfigurationError("GOOGLE_MAPS_API_KEY (invalid or restricted)")
    elif status == "OVER_QUERY_LIMIT":
        from agent.exceptions import RateLimitError
        raise RateLimitError(retry_after=60)
    elif status not in ("OK", "ZERO_RESULTS"):
        # Unknown error status - log and return not found
        log_warning(f"Geocoding unexpected status", place=place_name, status=status)
        return {
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "found": False,
            "error": status
        }
    
    # Extract results
    results = response.get("results", [])
    
    if not results or status == "ZERO_RESULTS":
        log_debug(f"Geocoding: no results", place=place_name)
        return {
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "found": False,
            "error": "ZERO_RESULTS"
        }
    
    # Get the first (best) result
    first_result = results[0]
    location = first_result["geometry"]["location"]
    formatted_address = first_result.get("formatted_address", place_name)
    
    log_debug(f"Geocoded successfully", address=formatted_address, 
              lat=location['lat'], lon=location['lng'])
    
    return {
        "latitude": location["lat"],
        "longitude": location["lng"],
        "formatted_address": formatted_address,
        "found": True
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def geocode_if_needed(
    lat: float | None,
    lon: float | None,
    place_name: str | None
) -> tuple[float, float, str | None]:
    """
    Geocode a place name if coordinates are not provided.
    
    This is a convenience function for the orchestrator.
    
    Args:
        lat: Latitude (if provided)
        lon: Longitude (if provided)
        place_name: Place name to geocode (if coords not provided)
        
    Returns:
        Tuple of (latitude, longitude, formatted_address)
        
    Raises:
        ValueError: If neither coords nor place_name provided,
                   or if geocoding fails
    """
    # If coordinates provided, use them directly
    if lat is not None and lon is not None:
        return lat, lon, None
    
    # If place name provided, geocode it
    if place_name:
        result = await geocode_place(place_name)
        
        if not result["found"]:
            raise GeocodingError(place_name, result.get("error", "Unknown"))
        
        return result["latitude"], result["longitude"], result["formatted_address"]
    
    # Neither provided
    raise ValueError(
        "Please provide either coordinates (latitude, longitude) "
        "or a place name."
    )


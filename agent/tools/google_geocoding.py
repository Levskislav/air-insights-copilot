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
    
    # Get API key from environment
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not api_key or api_key == "replace_me":
        raise ValueError(
            "GOOGLE_MAPS_API_KEY not configured. "
            "Add it to your .env file."
        )
    
    print(f"[geocoding] Looking up: '{place_name}'...")
    
    # Build query parameters
    params = {
        "address": place_name,
        "key": api_key,
        "language": language  # Response language
    }
    
    # Get timeout from environment
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10.0"))
    
    try:
        # Make the API call
        response = await request_with_retry(
            method="GET",
            url=GEOCODE_URL,
            params=params,
            timeout=timeout
        )
        
        # Check API status
        status = response.get("status", "UNKNOWN_ERROR")
        
        if status != "OK":
            # No results or error
            print(f"[geocoding] Status: {status}")
            return {
                "latitude": None,
                "longitude": None,
                "formatted_address": None,
                "found": False,
                "error": status
            }
        
        # Extract first result (most relevant)
        results = response.get("results", [])
        
        if not results:
            print("[geocoding] No results found")
            return {
                "latitude": None,
                "longitude": None,
                "formatted_address": None,
                "found": False,
                "error": "NO_RESULTS"
            }
        
        # Get the first (best) result
        first_result = results[0]
        location = first_result["geometry"]["location"]
        formatted_address = first_result.get("formatted_address", place_name)
        
        print(f"[geocoding] Found: {formatted_address}")
        print(f"[geocoding] Coordinates: ({location['lat']}, {location['lng']})")
        
        return {
            "latitude": location["lat"],
            "longitude": location["lng"],
            "formatted_address": formatted_address,
            "found": True
        }
        
    except Exception as e:
        print(f"[geocoding] Error: {e}")
        return {
            "latitude": None,
            "longitude": None,
            "formatted_address": None,
            "found": False,
            "error": str(e)
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
            raise ValueError(
                f"Could not find location: '{place_name}'. "
                f"Error: {result.get('error', 'Unknown')}"
            )
        
        return result["latitude"], result["longitude"], result["formatted_address"]
    
    # Neither provided
    raise ValueError(
        "Please provide either coordinates (latitude, longitude) "
        "or a place name."
    )


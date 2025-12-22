"""
agent/tools/nasa_apod.py
========================
NASA Astronomy Picture of the Day (APOD) API integration.

NASA APOD is a free API that returns a different astronomy image each day.
API Key: You can use "DEMO_KEY" for testing (limited requests)
         or get a free key at https://api.nasa.gov/

Endpoint: https://api.nasa.gov/planetary/apod
"""

import os
from typing import Any

from agent.retry import request_with_retry

# =============================================================================
# CONFIGURATION
# =============================================================================

# NASA APOD API endpoint
APOD_URL = "https://api.nasa.gov/planetary/apod"


# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def fetch_apod_today() -> dict[str, Any]:
    """
    Fetch NASA's Astronomy Picture of the Day.
    
    Returns:
        Raw JSON response from NASA containing:
        - title: Title of the image
        - url: URL to the image (or video)
        - explanation: Scientific explanation
        - date: Date of the picture
        - media_type: "image" or "video"
        
    Example response:
        {
            "title": "The Andromeda Galaxy",
            "url": "https://apod.nasa.gov/apod/image/...",
            "explanation": "The Andromeda Galaxy is...",
            "date": "2024-12-23",
            "media_type": "image"
        }
    """
    # Get API key from environment, default to DEMO_KEY
    # DEMO_KEY works but has rate limits (30 requests/hour)
    api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    
    # Build query parameters
    params = {
        "api_key": api_key
    }
    
    # Get timeout from environment or use default
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10.0"))
    
    print(f"[nasa] Fetching APOD (key: {'custom' if api_key != 'DEMO_KEY' else 'DEMO_KEY'})...")
    
    # Make the API call with retry support
    response = await request_with_retry(
        method="GET",
        url=APOD_URL,
        params=params,
        timeout=timeout
    )
    
    print(f"[nasa] Got APOD: {response.get('title', 'Unknown')}")
    
    return response
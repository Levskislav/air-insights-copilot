"""
agent/tools/google_directions.py
================================
Google Maps Directions API integration.

Gets route waypoints along a driving route from A to B.

API Endpoint: https://maps.googleapis.com/maps/api/directions/json
Authentication: Google Maps API Key (same as Geocoding)

Used for: Route Weather feature - getting weather at points along a journey.
"""

import os
from typing import Any

from agent.retry import request_with_retry

# =============================================================================
# CONFIGURATION
# =============================================================================

# Google Directions API endpoint
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def get_route_waypoints(
    origin: str, 
    destination: str, 
    num_points: int = 5
) -> dict[str, Any]:
    """
    Get waypoints along a driving route from origin to destination.
    
    Args:
        origin: Starting point (e.g., "Sofia" or "Sofia, Bulgaria")
        destination: End point (e.g., "Plovdiv" or "Plovdiv, Bulgaria")
        num_points: Number of waypoints to sample along the route (default 5)
        
    Returns:
        Dictionary with route info and waypoints:
        {
            "found": True,
            "origin_address": "Sofia, Bulgaria",
            "destination_address": "Plovdiv, Bulgaria",
            "total_distance_km": 145.5,
            "total_duration_minutes": 98,
            "waypoints": [
                {
                    "lat": 42.6977,
                    "lng": 23.3219,
                    "eta_minutes": 0,
                    "location_name": "Sofia, Bulgaria"
                },
                {
                    "lat": 42.4502,
                    "lng": 24.7520,
                    "eta_minutes": 49,
                    "location_name": "On route"
                },
                ...
            ]
        }
        
    Raises:
        ValueError: If GOOGLE_MAPS_API_KEY is not configured
    """
    
    # Get API key from environment
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not api_key or api_key == "replace_me":
        raise ValueError(
            "GOOGLE_MAPS_API_KEY not configured. "
            "Add it to your .env file."
        )
    
    print(f"[directions] Getting route: '{origin}' → '{destination}'...")
    
    # Build query parameters
    params = {
        "origin": origin,
        "destination": destination,
        "mode": "driving",
        "key": api_key,
        "language": "en"
    }
    
    # Get timeout from environment
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10.0"))
    
    try:
        # Make the API call
        response = await request_with_retry(
            method="GET",
            url=DIRECTIONS_URL,
            params=params,
            timeout=timeout
        )
        
        # Check API status
        status = response.get("status", "UNKNOWN_ERROR")
        
        if status != "OK":
            print(f"[directions] Status: {status}")
            return {
                "found": False,
                "error": status,
                "waypoints": []
            }
        
        # Extract route info
        routes = response.get("routes", [])
        
        if not routes:
            print("[directions] No routes found")
            return {
                "found": False,
                "error": "NO_ROUTES",
                "waypoints": []
            }
        
        # Get the first (best) route
        route = routes[0]
        leg = route["legs"][0]  # Single leg for direct A→B route
        
        # Extract basic info
        origin_address = leg.get("start_address", origin)
        destination_address = leg.get("end_address", destination)
        total_distance_m = leg["distance"]["value"]  # meters
        total_duration_s = leg["duration"]["value"]  # seconds
        
        total_distance_km = round(total_distance_m / 1000, 1)
        total_duration_minutes = round(total_duration_s / 60)
        
        print(f"[directions] Route found: {total_distance_km} km, {total_duration_minutes} min")
        
        # Build waypoints list
        waypoints = []
        
        # Start point
        start_loc = leg["start_location"]
        waypoints.append({
            "lat": start_loc["lat"],
            "lng": start_loc["lng"],
            "eta_minutes": 0,
            "location_name": origin_address
        })
        
        # Sample intermediate points from steps
        steps = leg.get("steps", [])
        
        if steps and num_points > 2:
            # Calculate how many intermediate points we need
            intermediate_count = num_points - 2  # Excluding start and end
            
            # Accumulate duration to find good sampling points
            accumulated_duration = 0
            interval = total_duration_s / (num_points - 1) if num_points > 1 else total_duration_s
            
            next_sample_time = interval
            
            for step in steps:
                step_duration = step["duration"]["value"]
                accumulated_duration += step_duration
                
                # Check if we've passed a sampling point
                if accumulated_duration >= next_sample_time and len(waypoints) < num_points - 1:
                    end_loc = step["end_location"]
                    waypoints.append({
                        "lat": end_loc["lat"],
                        "lng": end_loc["lng"],
                        "eta_minutes": round(accumulated_duration / 60),
                        "location_name": "On route"
                    })
                    next_sample_time += interval
        
        # End point
        end_loc = leg["end_location"]
        waypoints.append({
            "lat": end_loc["lat"],
            "lng": end_loc["lng"],
            "eta_minutes": total_duration_minutes,
            "location_name": destination_address
        })
        
        print(f"[directions] Generated {len(waypoints)} waypoints")
        
        return {
            "found": True,
            "origin_address": origin_address,
            "destination_address": destination_address,
            "total_distance_km": total_distance_km,
            "total_duration_minutes": total_duration_minutes,
            "waypoints": waypoints
        }
        
    except Exception as e:
        print(f"[directions] Error: {e}")
        return {
            "found": False,
            "error": str(e),
            "waypoints": []
        }


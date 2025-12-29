"""
agent/orchestrator.py
=====================
The "brain" of the agent - coordinates all tools and logic.

This is the central orchestration module that implements the agentic flow:
1. Validate input
2. Check cache (return immediately if hit)
3. Create execution plan
4. Fetch data from external APIs
5. Validate API responses
6. Compute averages
7. Generate LLM guidance
8. Cache result
9. Return response

All the pieces we built (retry, cache, validate, compute, tools, LLM)
come together here.
"""

import asyncio

from agent.planner import plan_for_analyze
from agent.validate import validate_lat_lon, validate_open_meteo_payload
from agent.compute import safe_avg, round_or_none
from agent.cache import cache_key, cache_get, cache_set
from agent.tools.open_meteo import fetch_air_quality, fetch_weather, fetch_snow, fetch_road_conditions, interpret_weather_code
from agent.tools.github_models_llm import generate_guidance_text
from agent.tools.nasa_apod import fetch_apod_today
from agent.tools.google_geocoding import geocode_if_needed
from agent.tools.google_directions import get_route_waypoints

# =============================================================================
# CONSTANTS
# =============================================================================

# Attribution text required by Open-Meteo terms of service
ATTRIBUTION = "Weather data by Open-Meteo.com"


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

async def analyze_air_and_weather(
    lat: float | None = None, 
    lon: float | None = None, 
    place_name: str | None = None,
    hours: int = 6
) -> dict:
    """
    Main orchestration function for air quality and weather analysis.
    
    This function coordinates the entire agentic flow:
    0. Geocode place name (if provided instead of coordinates)
    1. Input validation
    2. Cache lookup
    3. Planning
    4. Data fetching
    5. Response validation
    6. Computation
    7. LLM reasoning
    8. Caching
    
    Args:
        lat: Latitude coordinate (-90 to 90). Optional if place_name provided.
        lon: Longitude coordinate (-180 to 180). Optional if place_name provided.
        place_name: Place name to geocode (e.g., "Sofia"). Optional if coords provided.
        hours: Number of hours to analyze (1-168)
        
    Returns:
        Dictionary matching AnalyzeResponse schema:
        {
            "pm25_avg": float | None,
            "pm10_avg": float | None,
            "temp_avg": float | None,
            "snowfall_sum": float | None,
            "snow_depth_avg": float | None,
            "guidance_text": str
        }
        
    Raises:
        ValueError: If input validation fails or geocoding fails
    """
    
    print(f"\n{'='*60}")
    if place_name:
        print(f"[orchestrator] Starting analysis for '{place_name}' - {hours}h")
    else:
        print(f"[orchestrator] Starting analysis for ({lat}, {lon}) - {hours}h")
    print(f"{'='*60}")
    
    # =========================================================================
    # STEP 0: Geocode place name if needed
    # =========================================================================
    if place_name or lat is None or lon is None:
        print("[orchestrator] Step 0: Geocoding place name...")
        lat, lon, formatted_address = await geocode_if_needed(lat, lon, place_name)
        if formatted_address:
            print(f"[orchestrator]   - Resolved to: {formatted_address}")
        print(f"[orchestrator]   - Coordinates: ({lat}, {lon})")
    
    # =========================================================================
    # STEP 1: Validate input
    # =========================================================================
    print("[orchestrator] Step 1: Validating input...")
    validate_lat_lon(lat, lon)
    
    # =========================================================================
    # STEP 2: Check cache
    # =========================================================================
    print("[orchestrator] Step 2: Checking cache...")
    key = cache_key(lat, lon, hours)
    cached_result = cache_get(key)
    
    if cached_result is not None:
        print("[orchestrator] Cache HIT - returning cached result")
        return cached_result
    
    print("[orchestrator] Cache MISS - fetching fresh data")
    
    # =========================================================================
    # STEP 3: Create execution plan
    # =========================================================================
    print("[orchestrator] Step 3: Creating execution plan...")
    plan = plan_for_analyze(lat, lon, hours)
    
    # =========================================================================
    # STEP 4: Fetch data from external APIs
    # =========================================================================
    print("[orchestrator] Step 4: Fetching data from APIs...")
    
    air_json = None
    wx_json = None
    snow_json = None
    
    # Fetch air quality if needed
    if plan.need_air:
        try:
            print("[orchestrator]   - Fetching air quality...")
            air_json = await fetch_air_quality(lat, lon, hours)
            print("[orchestrator]   - Air quality: OK")
        except Exception as e:
            print(f"[orchestrator]   - Air quality FAILED: {e}")
    
    # Fetch weather if needed
    if plan.need_weather:
        try:
            print("[orchestrator]   - Fetching weather...")
            wx_json = await fetch_weather(lat, lon, hours)
            print("[orchestrator]   - Weather: OK")
        except Exception as e:
            print(f"[orchestrator]   - Weather FAILED: {e}")
    
    # Fetch snow data (always fetch for winter info)
    try:
        print("[orchestrator]   - Fetching snow data...")
        snow_json = await fetch_snow(lat, lon, hours)
        print("[orchestrator]   - Snow data: OK")
    except Exception as e:
        print(f"[orchestrator]   - Snow data FAILED: {e}")
    
    # =========================================================================
    # STEP 5: Validate API responses
    # =========================================================================
    print("[orchestrator] Step 5: Validating API responses...")
    data, quality_flags = validate_open_meteo_payload(air_json, wx_json, hours)
    
    if quality_flags.has_issues():
        print(f"[orchestrator]   - Quality issues detected: {quality_flags}")
    else:
        print("[orchestrator]   - Data quality: Good")
    
    # =========================================================================
    # STEP 6: Compute averages
    # =========================================================================
    print("[orchestrator] Step 6: Computing averages...")
    
    pm25_avg = round_or_none(safe_avg(data.get("pm25")), 2)
    pm10_avg = round_or_none(safe_avg(data.get("pm10")), 2)
    temp_avg = round_or_none(safe_avg(data.get("temp")), 2)
    
    # Extract and compute snow data
    snowfall_list = None
    snow_depth_list = None
    
    if snow_json and "hourly" in snow_json:
        snowfall_list = snow_json["hourly"].get("snowfall", [])[:hours]
        snow_depth_list = snow_json["hourly"].get("snow_depth", [])[:hours]
    
    # Sum snowfall (total cm expected in the time window)
    snowfall_sum = None
    if snowfall_list:
        valid_snowfall = [s for s in snowfall_list if s is not None]
        if valid_snowfall:
            snowfall_sum = round(sum(valid_snowfall), 2)
    
    # Average snow depth (cm on ground)
    snow_depth_avg = round_or_none(safe_avg(snow_depth_list), 2)
    
    print(f"[orchestrator]   - PM2.5 avg: {pm25_avg}")
    print(f"[orchestrator]   - PM10 avg: {pm10_avg}")
    print(f"[orchestrator]   - Temp avg: {temp_avg}")
    print(f"[orchestrator]   - Snowfall sum: {snowfall_sum} cm")
    print(f"[orchestrator]   - Snow depth avg: {snow_depth_avg} cm")
    
    # =========================================================================
    # STEP 7: Generate LLM guidance
    # =========================================================================
    print("[orchestrator] Step 7: Generating LLM guidance...")
    
    guidance = await generate_guidance_text(
        pm25_avg=pm25_avg,
        pm10_avg=pm10_avg,
        temp_avg=temp_avg,
        snowfall_sum=snowfall_sum,
        snow_depth_avg=snow_depth_avg,
        hours=hours,
        lat=lat,
        lon=lon,
        flags=quality_flags
    )
    
    # =========================================================================
    # STEP 8: Add attribution (required by Open-Meteo)
    # =========================================================================
    # Ensure attribution is always present
    if ATTRIBUTION not in guidance:
        guidance = guidance.strip()
        if guidance:
            guidance = f"{guidance}\n\n{ATTRIBUTION}"
        else:
            guidance = ATTRIBUTION
    
    # =========================================================================
    # STEP 9: Build response and cache
    # =========================================================================
    print("[orchestrator] Step 8: Building response and caching...")
    
    result = {
        "pm25_avg": pm25_avg,
        "pm10_avg": pm10_avg,
        "temp_avg": temp_avg,
        "snowfall_sum": snowfall_sum,
        "snow_depth_avg": snow_depth_avg,
        "guidance_text": guidance
    }
    
    # Cache the result for future requests
    cache_set(key, result)
    
    print(f"[orchestrator] Analysis complete!")
    print(f"{'='*60}\n")
    
    return result


# =============================================================================
# NASA APOD FUNCTION
# =============================================================================

async def apod_today() -> dict:
    """
    Fetch NASA's Astronomy Picture of the Day.
    
    This is a simpler function - just fetches and formats the APOD data.
    
    Returns:
        Dictionary matching ApodResponse schema:
        {
            "title": str,
            "url": str,
            "explanation": str
        }
    """
    print("[orchestrator] Fetching NASA APOD...")
    
    # Fetch from NASA API
    apod_data = await fetch_apod_today()
    
    # Extract and return relevant fields
    result = {
        "title": apod_data.get("title", "Unknown"),
        "url": apod_data.get("url", ""),
        "explanation": apod_data.get("explanation", "No explanation available.")
    }
    
    print(f"[orchestrator] APOD: {result['title']}")
    
    return result


# =============================================================================
# ROUTE WEATHER FUNCTION
# =============================================================================

async def analyze_route_weather(
    origin: str,
    destination: str,
    departure_hours: int = 0
) -> dict:
    """
    Get weather forecast along a driving route from origin to destination.
    
    This function:
    1. Gets route waypoints from Google Directions
    2. Fetches weather/air/snow data for each waypoint
    3. Generates warnings and summary
    
    Args:
        origin: Starting point (e.g., "Sofia")
        destination: End point (e.g., "Plovdiv")
        departure_hours: Hours from now when departing (0 = now)
        
    Returns:
        Dictionary matching RouteWeatherResponse schema
    """
    
    print(f"\n{'='*60}")
    print(f"[route-weather] Route: '{origin}' → '{destination}'")
    print(f"[route-weather] Departure: {departure_hours}h from now")
    print(f"{'='*60}")
    
    # =========================================================================
    # STEP 1: Get route waypoints from Google Directions
    # =========================================================================
    print("[route-weather] Step 1: Getting route waypoints...")
    
    route_info = await get_route_waypoints(origin, destination, num_points=5)
    
    if not route_info.get("found"):
        raise ValueError(
            f"Could not find route from '{origin}' to '{destination}'. "
            f"Error: {route_info.get('error', 'Unknown')}"
        )
    
    waypoints = route_info["waypoints"]
    print(f"[route-weather]   - Found {len(waypoints)} waypoints")
    print(f"[route-weather]   - Distance: {route_info['total_distance_km']} km")
    print(f"[route-weather]   - Duration: {route_info['total_duration_minutes']} min")
    
    # =========================================================================
    # STEP 2: Fetch weather for each waypoint (in parallel)
    # =========================================================================
    print("[route-weather] Step 2: Fetching weather for waypoints...")
    
    async def get_waypoint_weather(wp: dict) -> dict:
        """Fetch comprehensive road conditions for a single waypoint."""
        lat, lng = wp["lat"], wp["lng"]
        
        # Calculate which forecast hour to look at
        # ETA + departure offset
        forecast_hour = departure_hours + (wp["eta_minutes"] // 60)
        forecast_hour = min(forecast_hour, 167)  # Max 168 hours
        
        try:
            # Fetch comprehensive road conditions + air quality
            road_task = fetch_road_conditions(lat, lng, hours=forecast_hour + 1)
            air_task = fetch_air_quality(lat, lng, hours=forecast_hour + 1)
            
            road, air = await asyncio.gather(road_task, air_task)
            
            # Helper to safely get value at index
            def get_value(data: dict, key: str, idx: int):
                if data and "hourly" in data:
                    arr = data["hourly"].get(key, [])
                    if idx < len(arr):
                        return arr[idx]
                return None
            
            # Extract all values at the forecast hour
            temp = get_value(road, "temperature_2m", forecast_hour)
            rain = get_value(road, "rain", forecast_hour)
            showers = get_value(road, "showers", forecast_hour)
            snowfall = get_value(road, "snowfall", forecast_hour)
            snow_depth = get_value(road, "snow_depth", forecast_hour)
            visibility_m = get_value(road, "visibility", forecast_hour)
            wind_speed = get_value(road, "wind_speed_10m", forecast_hour)
            wind_gusts = get_value(road, "wind_gusts_10m", forecast_hour)
            weather_code = get_value(road, "weather_code", forecast_hour)
            cloud_cover = get_value(road, "cloud_cover", forecast_hour)
            precip_prob = get_value(road, "precipitation_probability", forecast_hour)
            pm25 = get_value(air, "pm2_5", forecast_hour)
            
            # Combine rain + showers
            total_rain = (rain or 0) + (showers or 0)
            
            # Convert visibility from meters to km
            visibility_km = round(visibility_m / 1000, 1) if visibility_m else None
            
            # Get human-readable conditions from weather code
            conditions = interpret_weather_code(weather_code)
            
            # Determine road warnings
            road_warning = None
            warnings_list = []
            
            if temp is not None and temp < 0:
                warnings_list.append("Icy roads possible ❄️")
            
            if visibility_km is not None and visibility_km < 1:
                warnings_list.append("Very low visibility 🌫️")
            elif visibility_km is not None and visibility_km < 5:
                warnings_list.append("Reduced visibility 🌫️")
            
            if wind_gusts and wind_gusts > 60:
                warnings_list.append("Strong wind gusts 💨")
            
            if snowfall and snowfall > 1:
                warnings_list.append("Heavy snow - slow driving 🌨️")
            
            if total_rain and total_rain > 5:
                warnings_list.append("Heavy rain - reduced grip 🌧️")
            
            if warnings_list:
                road_warning = " | ".join(warnings_list)
            
            return {
                "location_name": wp["location_name"],
                "latitude": round(lat, 4),
                "longitude": round(lng, 4),
                "eta_minutes": wp["eta_minutes"],
                "temperature": round(temp, 1) if temp is not None else None,
                "rain": round(total_rain, 1) if total_rain else None,
                "snowfall": round(snowfall, 2) if snowfall else None,
                "snow_depth": round(snow_depth, 1) if snow_depth else None,
                "precipitation_probability": int(precip_prob) if precip_prob is not None else None,
                "visibility": visibility_km,
                "wind_speed": round(wind_speed, 1) if wind_speed else None,
                "wind_gusts": round(wind_gusts, 1) if wind_gusts else None,
                "cloud_cover": int(cloud_cover) if cloud_cover is not None else None,
                "pm25": round(pm25, 1) if pm25 is not None else None,
                "weather_code": int(weather_code) if weather_code is not None else None,
                "conditions": conditions,
                "road_warning": road_warning
            }
            
        except Exception as e:
            print(f"[route-weather]   - Error for waypoint: {e}")
            return {
                "location_name": wp["location_name"],
                "latitude": round(lat, 4),
                "longitude": round(lng, 4),
                "eta_minutes": wp["eta_minutes"],
                "temperature": None,
                "rain": None,
                "snowfall": None,
                "snow_depth": None,
                "precipitation_probability": None,
                "visibility": None,
                "wind_speed": None,
                "wind_gusts": None,
                "cloud_cover": None,
                "pm25": None,
                "weather_code": None,
                "conditions": "Unknown",
                "road_warning": None
            }
    
    # Fetch all waypoints in parallel
    tasks = [get_waypoint_weather(wp) for wp in waypoints]
    waypoint_weather = await asyncio.gather(*tasks)
    
    print(f"[route-weather]   - Weather data collected for {len(waypoint_weather)} points")
    
    # =========================================================================
    # STEP 3: Generate warnings
    # =========================================================================
    print("[route-weather] Step 3: Generating warnings...")
    
    warnings = []
    
    for wp in waypoint_weather:
        loc = wp["location_name"]
        
        # Snow warnings
        if wp.get("snowfall") and wp["snowfall"] > 0.5:
            warnings.append(f"🌨️ Snow: {wp['snowfall']} cm near {loc}")
        
        # Rain warnings
        if wp.get("rain") and wp["rain"] > 5:
            warnings.append(f"🌧️ Heavy rain: {wp['rain']} mm near {loc}")
        
        # Temperature warnings (icy roads)
        if wp.get("temperature") is not None and wp["temperature"] < 0:
            warnings.append(f"❄️ Icy roads risk: {wp['temperature']}°C at {loc}")
        
        # Fog / visibility warnings
        if wp.get("visibility") is not None and wp["visibility"] < 1:
            warnings.append(f"🌫️ Very low visibility: {wp['visibility']} km at {loc}")
        elif wp.get("visibility") is not None and wp["visibility"] < 5:
            warnings.append(f"🌫️ Reduced visibility: {wp['visibility']} km at {loc}")
        
        # Wind warnings
        if wp.get("wind_gusts") and wp["wind_gusts"] > 60:
            warnings.append(f"💨 Strong gusts: {wp['wind_gusts']} km/h near {loc}")
        
        # Air quality warnings
        if wp.get("pm25") and wp["pm25"] > 50:
            warnings.append(f"😷 Poor air quality: PM2.5 {wp['pm25']} near {loc}")
    
    # Remove duplicates while preserving order
    warnings = list(dict.fromkeys(warnings))
    
    print(f"[route-weather]   - Generated {len(warnings)} warnings")
    
    # =========================================================================
    # STEP 4: Generate summary
    # =========================================================================
    print("[route-weather] Step 4: Generating summary...")
    
    temps = [wp["temperature"] for wp in waypoint_weather if wp.get("temperature") is not None]
    snow_total = sum(wp.get("snowfall") or 0 for wp in waypoint_weather)
    rain_total = sum(wp.get("rain") or 0 for wp in waypoint_weather)
    min_visibility = min((wp.get("visibility") for wp in waypoint_weather if wp.get("visibility") is not None), default=None)
    max_wind = max((wp.get("wind_gusts") or 0 for wp in waypoint_weather), default=0)
    
    summary_parts = []
    summary_parts.append(f"🚗 Route: {route_info['origin_address']} → {route_info['destination_address']}")
    summary_parts.append(f"📍 Distance: {route_info['total_distance_km']} km, ~{route_info['total_duration_minutes']} min")
    
    # Temperature
    if temps:
        min_temp = min(temps)
        max_temp = max(temps)
        summary_parts.append(f"🌡️ Temperature: {min_temp}°C to {max_temp}°C")
    
    # Precipitation
    if snow_total > 0:
        summary_parts.append(f"🌨️ Snowfall: {snow_total:.1f} cm expected")
    if rain_total > 0:
        summary_parts.append(f"🌧️ Rain: {rain_total:.1f} mm expected")
    if snow_total == 0 and rain_total == 0:
        summary_parts.append("☀️ No precipitation expected")
    
    # Visibility
    if min_visibility is not None and min_visibility < 5:
        summary_parts.append(f"🌫️ Low visibility: down to {min_visibility} km")
    
    # Wind
    if max_wind > 50:
        summary_parts.append(f"💨 Strong winds: gusts up to {max_wind} km/h")
    
    # Road conditions alerts
    alerts = []
    if any(wp.get("temperature") is not None and wp["temperature"] < 0 for wp in waypoint_weather):
        alerts.append("icy roads")
    if min_visibility is not None and min_visibility < 1:
        alerts.append("very low visibility")
    if snow_total > 2:
        alerts.append("snowy conditions")
    
    if alerts:
        summary_parts.append(f"⚠️ CAUTION: {', '.join(alerts)}")
    else:
        summary_parts.append("✅ Road conditions look good")
    
    summary = ". ".join(summary_parts) + f".\n\n{ATTRIBUTION}"
    
    # =========================================================================
    # STEP 5: Build response
    # =========================================================================
    print("[route-weather] Step 5: Building response...")
    
    result = {
        "origin": route_info["origin_address"],
        "destination": route_info["destination_address"],
        "total_distance_km": route_info["total_distance_km"],
        "total_duration_minutes": route_info["total_duration_minutes"],
        "waypoints": waypoint_weather,
        "summary": summary,
        "warnings": warnings
    }
    
    print(f"[route-weather] Route weather analysis complete!")
    print(f"{'='*60}\n")
    
    return result
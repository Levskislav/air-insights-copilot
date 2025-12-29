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

import time
import asyncio

from agent.planner import plan_for_analyze
from agent.validate import validate_lat_lon, validate_open_meteo_payload
from agent.compute import safe_avg, round_or_none
from agent.cache import cache_key, cache_get, cache_set
from agent.tools.open_meteo import fetch_air_quality, fetch_weather, fetch_snow
from agent.tools.github_models_llm import generate_guidance_text
from agent.tools.nasa_apod import fetch_apod_today
from agent.tools.google_geocoding import geocode_if_needed
from agent.logging_config import log_info, log_debug, log_warning, log_api_call, log_cache
from service.schemas import AnalyzeResponse, ApodResponse

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
) -> AnalyzeResponse:
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
    
    location_str = place_name if place_name else f"({lat}, {lon})"
    log_info(f"Starting analysis for {location_str}", hours=hours)
    
    # =========================================================================
    # STEP 0: Geocode place name if needed
    # =========================================================================
    if place_name or lat is None or lon is None:
        log_debug("Geocoding place name...")
        lat, lon, formatted_address = await geocode_if_needed(lat, lon, place_name)
        if formatted_address:
            log_info(f"Geocoded '{place_name}'", address=formatted_address, lat=lat, lon=lon)
    
    # =========================================================================
    # STEP 1: Validate input
    # =========================================================================
    log_debug("Validating input...")
    validate_lat_lon(lat, lon)
    
    # =========================================================================
    # STEP 2: Check cache
    # =========================================================================
    key = cache_key(lat, lon, hours)
    cached_result = cache_get(key)
    
    if cached_result is not None:
        log_cache("check", key, hit=True)
        return AnalyzeResponse(**cached_result)
    
    log_cache("check", key, hit=False)
    
    # =========================================================================
    # STEP 3: Create execution plan
    # =========================================================================
    log_debug("Creating execution plan...")
    plan = plan_for_analyze(lat, lon, hours)
    
    # =========================================================================
    # STEP 4: Fetch data from external APIs
    # =========================================================================
    log_debug("Fetching data from APIs...")
    
    start = time.perf_counter()
    
    # Create coroutines for parallel execution
    air_coro = fetch_air_quality(lat, lon, hours) if plan.need_air else None
    wx_coro = fetch_weather(lat, lon, hours) if plan.need_weather else None
    snow_coro = fetch_snow(lat, lon, hours)  # Always fetch snow for winter info
    
    # Build tasks list (only non-None coroutines)
    tasks = []
    task_map = {}  # Maps index to task name
    
    if air_coro:
        task_map[len(tasks)] = "air"
        tasks.append(air_coro)
    if wx_coro:
        task_map[len(tasks)] = "weather"
        tasks.append(wx_coro)
    if snow_coro:
        task_map[len(tasks)] = "snow"
        tasks.append(snow_coro)
    
    # Execute all API calls in parallel - return_exceptions=True prevents one failure from canceling others
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_duration = (time.perf_counter() - start) * 1000
    log_debug(f"All API calls completed in {total_duration:.0f}ms")
    
    # Extract results and handle exceptions
    air_json = None
    wx_json = None
    snow_json = None
    
    for idx, result in enumerate(results):
        task_name = task_map.get(idx)
        is_error = isinstance(result, Exception)
        
        if task_name == "air":
            if is_error:
                log_api_call("Open-Meteo", "air-quality", False, total_duration, error=str(result))
            else:
                air_json = result
                log_api_call("Open-Meteo", "air-quality", True, total_duration)
        elif task_name == "weather":
            if is_error:
                log_api_call("Open-Meteo", "forecast", False, total_duration, error=str(result))
            else:
                wx_json = result
                log_api_call("Open-Meteo", "forecast", True, total_duration)
        elif task_name == "snow":
            if is_error:
                log_api_call("Open-Meteo", "snow", False, total_duration, error=str(result))
            else:
                snow_json = result
                log_api_call("Open-Meteo", "snow", True, total_duration)
    
    # =========================================================================
    # STEP 5: Validate API responses
    # =========================================================================
    log_debug("Validating API responses...")
    data, quality_flags = validate_open_meteo_payload(air_json, wx_json, hours)
    
    if quality_flags.has_issues():
        log_warning("Data quality issues", flags=str(quality_flags))
    
    # =========================================================================
    # STEP 6: Compute averages
    # =========================================================================
    log_debug("Computing averages...")
    
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
    
    log_debug("Computed averages", pm25=pm25_avg, pm10=pm10_avg, temp=temp_avg, 
              snowfall=snowfall_sum, snow_depth=snow_depth_avg)
    
    # =========================================================================
    # STEP 7: Generate LLM guidance
    # =========================================================================
    log_debug("Generating LLM guidance...")
    
    start = time.perf_counter()
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
    log_api_call("GitHub-Models", "LLM", True, (time.perf_counter() - start) * 1000)
    
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
    result = AnalyzeResponse(
        pm25_avg=pm25_avg,
        pm10_avg=pm10_avg,
        temp_avg=temp_avg,
        snowfall_sum=snowfall_sum,
        snow_depth_avg=snow_depth_avg,
        guidance_text=guidance
    )
    
    # Cache the result for future requests (as dict for serialization)
    cache_set(key, result.model_dump())
    log_cache("set", key)
    
    log_info("Analysis complete", lat=lat, lon=lon, hours=hours)
    
    return result


# =============================================================================
# NASA APOD FUNCTION
# =============================================================================

async def apod_today() -> ApodResponse:
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
    log_debug("Fetching NASA APOD...")
    
    start = time.perf_counter()
    try:
        apod_data = await fetch_apod_today()
        log_api_call("NASA", "APOD", True, (time.perf_counter() - start) * 1000)
    except Exception as e:
        log_api_call("NASA", "APOD", False, (time.perf_counter() - start) * 1000, error=str(e))
        raise
    
    result = ApodResponse(
        title=apod_data.get("title", "Unknown"),
        url=apod_data.get("url", ""),
        explanation=apod_data.get("explanation", "No explanation available.")
    )
    
    log_info(f"APOD fetched", title=result.title)
    
    return result

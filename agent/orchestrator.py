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

from agent.planner import plan_for_analyze
from agent.validate import validate_lat_lon, validate_open_meteo_payload
from agent.compute import safe_avg, round_or_none
from agent.cache import cache_key, cache_get, cache_set
from agent.tools.open_meteo import fetch_air_quality, fetch_weather
from agent.tools.github_models_llm import generate_guidance_text
from agent.tools.nasa_apod import fetch_apod_today

# =============================================================================
# CONSTANTS
# =============================================================================

# Attribution text required by Open-Meteo terms of service
ATTRIBUTION = "Weather data by Open-Meteo.com"


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

async def analyze_air_and_weather(lat: float, lon: float, hours: int) -> dict:
    """
    Main orchestration function for air quality and weather analysis.
    
    This function coordinates the entire agentic flow:
    1. Input validation
    2. Cache lookup
    3. Planning
    4. Data fetching
    5. Response validation
    6. Computation
    7. LLM reasoning
    8. Caching
    
    Args:
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate (-180 to 180)
        hours: Number of hours to analyze (1-168)
        
    Returns:
        Dictionary matching AnalyzeResponse schema:
        {
            "pm25_avg": float | None,
            "pm10_avg": float | None,
            "temp_avg": float | None,
            "guidance_text": str
        }
        
    Raises:
        ValueError: If input validation fails
    """
    
    print(f"\n{'='*60}")
    print(f"[orchestrator] Starting analysis for ({lat}, {lon}) - {hours}h")
    print(f"{'='*60}")
    
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
    
    print(f"[orchestrator]   - PM2.5 avg: {pm25_avg}")
    print(f"[orchestrator]   - PM10 avg: {pm10_avg}")
    print(f"[orchestrator]   - Temp avg: {temp_avg}")
    
    # =========================================================================
    # STEP 7: Generate LLM guidance
    # =========================================================================
    print("[orchestrator] Step 7: Generating LLM guidance...")
    
    guidance = await generate_guidance_text(
        pm25_avg=pm25_avg,
        pm10_avg=pm10_avg,
        temp_avg=temp_avg,
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
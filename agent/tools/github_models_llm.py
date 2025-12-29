"""
agent/tools/github_models_llm.py
================================
GitHub Models integration for LLM-powered guidance generation.

GitHub Models provides FREE inference for various LLMs.
We use it to turn numeric data into human-friendly guidance.

API Endpoint: https://models.github.ai/inference/chat/completions
Authentication: GitHub Personal Access Token (PAT)

If LLM fails (timeout, rate limit, etc.), we return a rule-based fallback.
"""

import os
from pathlib import Path

from agent.retry import request_with_retry
from agent.validate import QualityFlags
from agent.logging_config import log_debug, log_warning
from agent.config import (
    PM25_GOOD_THRESHOLD, PM25_MODERATE_THRESHOLD,
    TEMP_FREEZING, TEMP_COLD, TEMP_COOL, TEMP_HOT,
    DEFAULT_LLM_TIMEOUT_SECONDS
)

# =============================================================================
# CONFIGURATION
# =============================================================================

# GitHub Models API endpoint (OpenAI-compatible)
GITHUB_MODELS_URL = "https://models.github.ai/inference/chat/completions"

# Path to prompt templates
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


# =============================================================================
# PROMPT LOADING
# =============================================================================

def _load_prompt(filename: str) -> str:
    """
    Load a prompt template from the prompts directory.
    
    Args:
        filename: Name of the prompt file (e.g., "guidance_system.txt")
        
    Returns:
        The prompt text
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    filepath = PROMPTS_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def _build_messages(
    pm25_avg: float | None,
    pm10_avg: float | None,
    temp_avg: float | None,
    snowfall_sum: float | None,
    snow_depth_avg: float | None,
    hours: int,
    lat: float,
    lon: float,
    flags: QualityFlags
) -> list[dict[str, str]]:
    """
    Build the messages array for the LLM API call.
    
    This creates the system prompt and user prompt with all the data.
    
    Args:
        pm25_avg: Average PM2.5 concentration
        pm10_avg: Average PM10 concentration
        temp_avg: Average temperature
        snowfall_sum: Total snowfall in cm
        snow_depth_avg: Average snow depth in cm
        hours: Time window in hours
        lat: Latitude
        lon: Longitude
        flags: Data quality flags
        
    Returns:
        List of message dictionaries for the API
    """
    # Load prompts from files
    system_prompt = _load_prompt("guidance_system.txt")
    user_template = _load_prompt("guidance_user_template.txt")
    
    # Format the user prompt with actual data
    user_prompt = user_template.format(
        lat=lat,
        lon=lon,
        hours=hours,
        pm25=pm25_avg if pm25_avg is not None else "N/A",
        pm10=pm10_avg if pm10_avg is not None else "N/A",
        temp=temp_avg if temp_avg is not None else "N/A",
        snowfall_sum=snowfall_sum if snowfall_sum is not None else "N/A",
        snow_depth_avg=snow_depth_avg if snow_depth_avg is not None else "N/A",
        sparse_air=flags.sparse_air,
        sparse_weather=flags.sparse_weather,
        missing_fields=", ".join(flags.missing_fields) if flags.missing_fields else "none"
    )
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


# =============================================================================
# FALLBACK GUIDANCE
# =============================================================================

def _fallback_guidance(
    pm25_avg: float | None,
    pm10_avg: float | None,
    temp_avg: float | None,
    snowfall_sum: float | None,
    snow_depth_avg: float | None,
    hours: int,
    flags: QualityFlags
) -> str:
    """
    Generate rule-based fallback guidance when LLM is unavailable.
    
    This ensures the API always returns something useful,
    even if GitHub Models is down or rate limited.
    
    Args:
        pm25_avg: Average PM2.5 concentration
        pm10_avg: Average PM10 concentration
        temp_avg: Average temperature
        snowfall_sum: Total snowfall in cm
        snow_depth_avg: Average snow depth in cm
        hours: Time window in hours
        flags: Data quality flags
        
    Returns:
        Simple guidance text based on thresholds
    """
    parts = []
    recommendations = []
    
    # Time window info
    if hours == 1:
        parts.append("Current conditions:")
    else:
        parts.append(f"Forecast for the next {hours} hours:")
    
    # Data quality warning
    if flags.has_issues():
        parts.append("⚠️ Note: Some data is incomplete.")
    
    # PM2.5 assessment (WHO guidelines)
    air_quality = "unknown"
    if pm25_avg is not None:
        if pm25_avg <= PM25_GOOD_THRESHOLD:
            parts.append(f"Air quality is excellent (PM2.5: {pm25_avg:.1f} μg/m³).")
            air_quality = "good"
        elif pm25_avg <= PM25_MODERATE_THRESHOLD:
            parts.append(f"Air quality is moderate (PM2.5: {pm25_avg:.1f} μg/m³).")
            air_quality = "moderate"
        else:
            parts.append(f"Air quality is poor (PM2.5: {pm25_avg:.1f} μg/m³).")
            air_quality = "poor"
    
    # Temperature assessment
    temp_category = "mild"
    if temp_avg is not None:
        if temp_avg < TEMP_FREEZING:
            parts.append(f"Very cold at {temp_avg:.1f}°C - risk of frostbite.")
            temp_category = "freezing"
        elif temp_avg < TEMP_COLD:
            parts.append(f"Cold at {temp_avg:.1f}°C.")
            temp_category = "cold"
        elif temp_avg < TEMP_COOL:
            parts.append(f"Cool at {temp_avg:.1f}°C.")
            temp_category = "cool"
        elif temp_avg < TEMP_HOT:
            parts.append(f"Pleasant {temp_avg:.1f}°C.")
            temp_category = "pleasant"
        else:
            parts.append(f"Hot at {temp_avg:.1f}°C - stay hydrated.")
            temp_category = "hot"
    
    # Snow assessment
    has_snow = False
    good_for_skiing = False
    if snowfall_sum is not None and snowfall_sum > 0:
        has_snow = True
        parts.append(f"🌨️ Snowfall: {snowfall_sum:.1f} cm expected.")
        if snowfall_sum > 5:
            recommendations.append("Roads may be slippery - drive carefully!")
    
    if snow_depth_avg is not None and snow_depth_avg > 0:
        has_snow = True
        parts.append(f"Snow on ground: {snow_depth_avg:.1f} cm.")
        if snow_depth_avg >= 30:
            good_for_skiing = True
    
    # Generate context-aware recommendations
    if good_for_skiing and air_quality in ["good", "moderate"]:
        recommendations.append("Great conditions for skiing or snowboarding! ⛷️")
    elif has_snow and temp_category in ["cold", "freezing"]:
        recommendations.append("Perfect weather for building a snowman or a winter walk. 🏔️")
    elif air_quality == "good" and temp_category == "pleasant":
        recommendations.append("Ideal conditions for jogging, cycling, or a picnic! 🚴")
    elif air_quality == "good" and temp_category in ["cool", "cold"]:
        recommendations.append("Good for a brisk walk or hiking - dress in layers! 🥾")
    elif air_quality == "good" and temp_category == "hot":
        recommendations.append("Best to exercise early morning or evening. Stay hydrated! 💧")
    elif air_quality == "moderate":
        recommendations.append("Light outdoor activities are fine. Sensitive individuals should take breaks.")
    elif air_quality == "poor":
        recommendations.append("Consider indoor activities today. If outdoors, limit exertion.")
    elif temp_category == "freezing":
        recommendations.append("Limit time outdoors. Wear warm layers and protect extremities. 🧤")
    else:
        recommendations.append("Check local conditions and plan accordingly. Enjoy your day! 🌤️")
    
    parts.extend(recommendations)
    
    # Attribution
    parts.append("Weather data by Open-Meteo.com.")
    
    return " ".join(parts)


# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def generate_guidance_text(
    *,
    pm25_avg: float | None,
    pm10_avg: float | None,
    temp_avg: float | None,
    snowfall_sum: float | None = None,
    snow_depth_avg: float | None = None,
    hours: int,
    lat: float,
    lon: float,
    flags: QualityFlags
) -> str:
    """
    Generate AI-powered guidance text using GitHub Models LLM.
    
    This function:
    1. Checks if GitHub token is configured
    2. Builds prompts with the weather/air data
    3. Calls GitHub Models API
    4. Falls back to rule-based guidance if LLM fails
    
    Args:
        pm25_avg: Average PM2.5 concentration (μg/m³)
        pm10_avg: Average PM10 concentration (μg/m³)
        temp_avg: Average temperature (°C)
        snowfall_sum: Total snowfall (cm) for the time window
        snow_depth_avg: Average snow depth (cm) on the ground
        hours: Time window in hours
        lat: Latitude
        lon: Longitude
        flags: Data quality flags
        
    Returns:
        Guidance text (either from LLM or fallback)
        
    Note:
        All arguments are keyword-only (*) to prevent mistakes.
    """
    # Get configuration from environment
    token = os.getenv("GITHUB_MODELS_TOKEN")
    model = os.getenv("GITHUB_MODELS_MODEL", "gpt-4o-mini")
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", str(DEFAULT_LLM_TIMEOUT_SECONDS)))
    
    # If no token configured, use fallback immediately
    if not token or token == "replace_me_with_your_github_pat":
        log_warning("No GitHub token configured, using fallback guidance")
        return _fallback_guidance(pm25_avg, pm10_avg, temp_avg, snowfall_sum, snow_depth_avg, hours, flags)
    
    try:
        # Build the messages for the LLM
        messages = _build_messages(
            pm25_avg, pm10_avg, temp_avg, snowfall_sum, snow_depth_avg,
            hours, lat, lon, flags
        )
        
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,  # Lower = more consistent responses
            "max_tokens": 300   # Limit response length
        }
        
        log_debug(f"Calling GitHub Models", model=model)
        
        # Make the API call with retry support
        response = await request_with_retry(
            method="POST",
            url=GITHUB_MODELS_URL,
            headers=headers,
            json=body,
            timeout=timeout
        )
        
        # Extract the generated text from response
        guidance = response["choices"][0]["message"]["content"]
        log_debug(f"LLM guidance generated", chars=len(guidance))
        
        return guidance.strip()
        
    except Exception as e:
        # LLM failed - log error and use fallback
        log_warning(f"GitHub Models error, using fallback", error=str(e))
        return _fallback_guidance(pm25_avg, pm10_avg, temp_avg, snowfall_sum, snow_depth_avg, hours, flags)
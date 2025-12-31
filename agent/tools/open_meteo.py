"""
agent/tools/open_meteo.py
=========================
Open-Meteo API integration for weather and air quality data.

Open-Meteo is a FREE weather API that requires NO API key!
Website: https://open-meteo.com/

We use two endpoints:
1. Air Quality API - for PM2.5 and PM10 (particulate matter)
2. Weather Forecast API - for temperature

API Response Format:
    {
        "hourly": {
            "time": ["2024-01-01T00:00", "2024-01-01T01:00", ...],
            "pm2_5": [10.5, 12.3, ...],
            "pm10": [15.2, 18.1, ...],
            "temperature_2m": [5.2, 4.8, ...]
        }
    }
"""

import os
from typing import Any

from agent.retry import request_with_retry
from agent.config import DEFAULT_HTTP_TIMEOUT_SECONDS

# =============================================================================
# API ENDPOINTS
# =============================================================================

# Open-Meteo Air Quality API (PM2.5, PM10, etc.)
# Docs: https://open-meteo.com/en/docs/air-quality-api
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Open-Meteo Weather Forecast API (temperature, humidity, etc.)
# Docs: https://open-meteo.com/en/docs
WEATHER_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


# =============================================================================
# AIR QUALITY FUNCTION
# =============================================================================

async def fetch_air_quality(lat: float, lon: float, hours: int) -> dict[str, Any]:
    """
    Fetch air quality data (PM2.5, PM10) from Open-Meteo.
    
    Args:
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate (-180 to 180)
        hours: Number of hours to forecast (1-168)
        
    Returns:
        Raw JSON response from Open-Meteo containing:
        - hourly.time: List of ISO timestamps
        - hourly.pm2_5: List of PM2.5 values (μg/m³)
        - hourly.pm10: List of PM10 values (μg/m³)
        
    Example response:
        {
            "latitude": 42.7,
            "longitude": 23.3,
            "hourly": {
                "time": ["2024-12-23T00:00", ...],
                "pm2_5": [10.5, 12.3, ...],
                "pm10": [15.2, 18.1, ...]
            }
        }
    """
    
    # Build query parameters for the API
    params = {
        "latitude": lat,
        "longitude": lon,
        # Request PM2.5 and PM10 in the hourly data
        "hourly": "pm2_5,pm10",
        # Limit forecast to requested hours
        "forecast_hours": hours,
        # Auto-detect timezone based on coordinates
        "timezone": "auto"
    }
    
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", str(DEFAULT_HTTP_TIMEOUT_SECONDS)))
    
    response = await request_with_retry(
        method="GET",
        url=AIR_QUALITY_URL,
        params=params,
        timeout=timeout
    )
    
    return response


# =============================================================================
# WEATHER FUNCTION
# =============================================================================

async def fetch_weather(lat: float, lon: float, hours: int) -> dict[str, Any]:
    """
    Fetch weather forecast data (temperature) from Open-Meteo.
    
    Args:
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate (-180 to 180)
        hours: Number of hours to forecast (1-168)
        
    Returns:
        Raw JSON response from Open-Meteo containing:
        - hourly.time: List of ISO timestamps
        - hourly.temperature_2m: List of temperatures (°C at 2m height)
        
    Example response:
        {
            "latitude": 42.7,
            "longitude": 23.3,
            "hourly": {
                "time": ["2024-12-23T00:00", ...],
                "temperature_2m": [5.2, 4.8, 6.1, ...]
            }
        }
        
    Note:
        Temperature is measured at 2 meters above ground level,
        which is the standard height for weather stations.
    """
    
    # Build query parameters for the API
    params = {
        "latitude": lat,
        "longitude": lon,
        # Request temperature at 2 meters height
        "hourly": "temperature_2m",
        # Limit forecast to requested hours
        "forecast_hours": hours,
        # Auto-detect timezone based on coordinates
        "timezone": "auto"
    }
    
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", str(DEFAULT_HTTP_TIMEOUT_SECONDS)))
    
    response = await request_with_retry(
        method="GET",
        url=WEATHER_FORECAST_URL,
        params=params,
        timeout=timeout
    )
    
    return response


# =============================================================================
# SNOW FUNCTION
# =============================================================================

async def fetch_snow(lat: float, lon: float, hours: int) -> dict[str, Any]:
    """
    Fetch snow data (snowfall, snow depth) from Open-Meteo.
    
    Args:
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate (-180 to 180)
        hours: Number of hours to forecast (1-168)
        
    Returns:
        Raw JSON response from Open-Meteo containing:
        - hourly.time: List of ISO timestamps
        - hourly.snowfall: List of snowfall values (cm per hour)
        - hourly.snow_depth: List of snow depth values (cm on ground)
        
    Example response:
        {
            "latitude": 42.7,
            "longitude": 23.3,
            "hourly": {
                "time": ["2024-12-23T00:00", ...],
                "snowfall": [0.0, 0.5, 1.2, ...],
                "snow_depth": [15.0, 15.5, 16.7, ...]
            }
        }
        
    Note:
        - snowfall: Amount of snow falling per hour (cm)
        - snow_depth: Total accumulated snow on the ground (cm)
    """
    
    # Build query parameters for the API
    params = {
        "latitude": lat,
        "longitude": lon,
        # Request snowfall and snow depth in the hourly data
        "hourly": "snowfall,snow_depth",
        # Limit forecast to requested hours
        "forecast_hours": hours,
        # Auto-detect timezone based on coordinates
        "timezone": "auto"
    }
    
    timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", str(DEFAULT_HTTP_TIMEOUT_SECONDS)))
    
    response = await request_with_retry(
        method="GET",
        url=WEATHER_FORECAST_URL,
        params=params,
        timeout=timeout
    )
    
    return response


"""
agent/validate.py
=================
Input validation and data quality checks.

This module provides:
1. Input validation (lat/lon bounds checking)
2. API response validation (check if data exists)
3. Data quality flags (sparse/missing data detection)

The quality flags are passed to the LLM so it can mention
uncertainty in its guidance when data is incomplete.
"""

from dataclasses import dataclass, field
from typing import Any

from agent.config import MAX_FORECAST_HOURS, MIN_FORECAST_HOURS


# =============================================================================
# DATA QUALITY FLAGS
# =============================================================================

@dataclass
class QualityFlags:
    """
    Flags indicating data quality issues.
    
    These flags are passed to the LLM so it can adjust its guidance
    based on data completeness. For example, if sparse_air=True,
    the LLM might say "Air quality data is incomplete, use caution."
    
    Attributes:
        sparse_air: True if air quality data has many missing values
        sparse_weather: True if weather data has many missing values
        missing_fields: List of field names that are completely missing
    """
    sparse_air: bool = False
    sparse_weather: bool = False
    missing_fields: list[str] = field(default_factory=list)
    
    def has_issues(self) -> bool:
        """Check if there are any data quality issues."""
        return self.sparse_air or self.sparse_weather or len(self.missing_fields) > 0


# =============================================================================
# INPUT VALIDATION
# =============================================================================

def validate_lat_lon(lat: float, lon: float) -> None:
    """
    Validate latitude and longitude coordinates.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        
    Raises:
        ValueError: If coordinates are out of valid range
        
    Example:
        >>> validate_lat_lon(42.6977, 23.3219)  # Sofia, Bulgaria - OK
        >>> validate_lat_lon(200.0, 23.0)  # Raises ValueError
    """
    # Check latitude bounds (North/South pole limits)
    if lat < -90 or lat > 90:
        raise ValueError(f"Latitude {lat} is out of range [-90, 90]")
    
    # Check longitude bounds (International Date Line limits)
    if lon < -180 or lon > 180:
        raise ValueError(f"Longitude {lon} is out of range [-180, 180]")


def validate_hours(hours: int) -> None:
    """
    Validate hours parameter.
    
    Args:
        hours: Number of hours to forecast
        
    Raises:
        ValueError: If hours is out of valid range
    """
    if hours < MIN_FORECAST_HOURS or hours > MAX_FORECAST_HOURS:
        raise ValueError(f"Hours {hours} is out of range [{MIN_FORECAST_HOURS}, {MAX_FORECAST_HOURS}]")


# =============================================================================
# API RESPONSE HELPERS
# =============================================================================

def _get_hourly_array(payload: dict | None, key: str) -> list | None:
    """
    Safely extract an hourly array from Open-Meteo response.
    
    Open-Meteo responses have structure:
        {"hourly": {"time": [...], "pm2_5": [...], ...}}
    
    This helper safely navigates this structure and returns
    the requested array, or None if it doesn't exist.
    
    Args:
        payload: The API response dictionary
        key: The key to extract (e.g., "pm2_5", "temperature_2m")
        
    Returns:
        The array of values, or None if not found
    """
    # Check if payload exists and is a dict
    if not isinstance(payload, dict):
        return None
    
    # Get the "hourly" section
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        return None
    
    # Get the requested array
    return hourly.get(key)


def _check_sparseness(values: list | None, threshold: float = 0.5) -> bool:
    """
    Check if a list of values is too sparse (many None/null values).
    
    Args:
        values: List of values (may contain None)
        threshold: Maximum allowed ratio of None values (default 0.5 = 50%)
        
    Returns:
        True if data is sparse (too many None values), False otherwise
    """
    if not values or len(values) == 0:
        return True  # Empty list is considered sparse
    
    # Count non-None values
    valid_count = sum(1 for v in values if v is not None)
    
    # Calculate ratio of valid values
    valid_ratio = valid_count / len(values)
    
    # Sparse if less than threshold of values are valid
    return valid_ratio < threshold


# =============================================================================
# MAIN VALIDATION FUNCTION
# =============================================================================

def validate_open_meteo_payload(
    air_json: dict | None,
    wx_json: dict | None,
    hours: int
) -> tuple[dict[str, list | None], QualityFlags]:
    """
    Validate and extract data from Open-Meteo API responses.
    
    This function:
    1. Extracts pm2_5, pm10, and temperature arrays
    2. Slices them to the requested number of hours
    3. Checks for missing/sparse data
    4. Returns quality flags for the LLM
    
    Args:
        air_json: Response from air quality API (or None if failed)
        wx_json: Response from weather API (or None if failed)
        hours: Number of hours requested (for slicing)
        
    Returns:
        Tuple of:
        - dict with keys: "pm25", "pm10", "temp" (values are lists or None)
        - QualityFlags indicating data quality issues
        
    Example:
        >>> data, flags = validate_open_meteo_payload(air_resp, wx_resp, 6)
        >>> if flags.sparse_air:
        ...     print("Warning: Air quality data is incomplete")
    """
    # Initialize quality flags
    flags = QualityFlags(missing_fields=[])
    
    # Initialize data containers
    pm25: list | None = None
    pm10: list | None = None
    temp: list | None = None
    
    # ==========================================================================
    # Extract air quality data
    # ==========================================================================
    if air_json:
        pm25 = _get_hourly_array(air_json, "pm2_5")
        pm10 = _get_hourly_array(air_json, "pm10")
        
        # Track missing fields
        if pm25 is None:
            flags.missing_fields.append("pm2_5")
        if pm10 is None:
            flags.missing_fields.append("pm10")
        
        # Check for sparse data
        flags.sparse_air = _check_sparseness(pm25) or _check_sparseness(pm10)
    else:
        # No air data at all
        flags.sparse_air = True
        flags.missing_fields.extend(["pm2_5", "pm10"])
    
    # ==========================================================================
    # Extract weather data
    # ==========================================================================
    if wx_json:
        temp = _get_hourly_array(wx_json, "temperature_2m")
        
        # Track missing fields
        if temp is None:
            flags.missing_fields.append("temperature_2m")
        
        # Check for sparse data
        flags.sparse_weather = _check_sparseness(temp)
    else:
        # No weather data at all
        flags.sparse_weather = True
        flags.missing_fields.append("temperature_2m")
    
    # ==========================================================================
    # Slice arrays to requested hours
    # ==========================================================================
    # Open-Meteo might return more hours than requested
    if pm25:
        pm25 = pm25[:hours]
    if pm10:
        pm10 = pm10[:hours]
    if temp:
        temp = temp[:hours]
    
    # Return extracted data and quality flags
    return {"pm25": pm25, "pm10": pm10, "temp": temp}, flags
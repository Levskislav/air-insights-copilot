"""
agent/cache.py
==============
In-memory TTL (Time-To-Live) cache for API responses.

Why cache?
1. Reduce external API calls (Open-Meteo, NASA, GitHub Models)
2. Faster response times for repeated requests
3. Protection against rate limiting
4. Cost savings (for paid APIs)

Cache key format: "lat:lon:hours" (e.g., "42.6977:23.3219:6")
Cache TTL: 10 minutes (600 seconds) - configurable via environment

Uses cachetools.TTLCache which automatically removes expired entries.
"""

import os
from typing import Any

from cachetools import TTLCache

# =============================================================================
# CONFIGURATION
# =============================================================================

# Get TTL from environment variable, default to 600 seconds (10 minutes)
# This allows easy configuration without code changes
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "600"))

# Maximum number of cached entries
# Prevents memory issues if many different locations are requested
CACHE_MAX_SIZE = 1024

# =============================================================================
# CREATE THE CACHE
# =============================================================================

# TTLCache automatically removes entries after TTL expires
# This is thread-safe for read operations
_cache: TTLCache = TTLCache(
    maxsize=CACHE_MAX_SIZE,
    ttl=CACHE_TTL_SECONDS
)


# =============================================================================
# CACHE KEY GENERATION
# =============================================================================

def cache_key(lat: float, lon: float, hours: int) -> str:
    """
    Generate a cache key from request parameters.
    
    The key uniquely identifies a request based on:
    - Latitude (rounded to 4 decimal places for ~11 meter precision)
    - Longitude (rounded to 4 decimal places)
    - Hours (exact value)
    
    Rounding coordinates prevents cache fragmentation from
    tiny floating-point differences (e.g., 42.6977 vs 42.69770001)
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        hours: Number of hours requested
        
    Returns:
        Cache key string like "42.6977:23.3219:6"
        
    Example:
        >>> cache_key(42.697712, 23.321899, 6)
        "42.6977:23.3219:6"
    """
    # Round to 4 decimal places (~11 meter precision)
    # This is accurate enough for weather data while reducing cache misses
    rounded_lat = round(lat, 4)
    rounded_lon = round(lon, 4)
    
    return f"{rounded_lat}:{rounded_lon}:{hours}"


# =============================================================================
# CACHE OPERATIONS
# =============================================================================

def cache_get(key: str) -> Any | None:
    """
    Get a value from the cache.
    
    Args:
        key: The cache key (from cache_key() function)
        
    Returns:
        The cached value, or None if not found or expired
        
    Example:
        >>> key = cache_key(42.6977, 23.3219, 6)
        >>> result = cache_get(key)
        >>> if result is not None:
        ...     print("Cache hit!")
    """
    result = _cache.get(key)
    
    # Log cache hit/miss for debugging
    if result is not None:
        print(f"[cache] HIT: {key}")
    else:
        print(f"[cache] MISS: {key}")
    
    return result


def cache_set(key: str, value: Any) -> None:
    """
    Store a value in the cache.
    
    The value will automatically expire after CACHE_TTL_SECONDS.
    
    Args:
        key: The cache key (from cache_key() function)
        value: The value to cache (typically a dict with API response)
        
    Example:
        >>> key = cache_key(42.6977, 23.3219, 6)
        >>> cache_set(key, {"pm25_avg": 12.5, "guidance_text": "..."})
    """
    _cache[key] = value
    print(f"[cache] SET: {key} (TTL: {CACHE_TTL_SECONDS}s)")


def cache_clear() -> None:
    """
    Clear all entries from the cache.
    
    Useful for testing or when you need fresh data.
    """
    _cache.clear()
    print("[cache] CLEARED all entries")


def cache_stats() -> dict:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache info:
        - size: Current number of cached entries
        - maxsize: Maximum allowed entries
        - ttl: Time-to-live in seconds
        
    Example:
        >>> stats = cache_stats()
        >>> print(f"Cache has {stats['size']} entries")
    """
    return {
        "size": len(_cache),
        "maxsize": CACHE_MAX_SIZE,
        "ttl": CACHE_TTL_SECONDS
    }
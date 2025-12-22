"""
agent/retry.py
==============
HTTP request helper with automatic retry and exponential backoff.

When calling external APIs, things can go wrong:
- Network hiccups (connection reset, timeout)
- Rate limiting (429 Too Many Requests)
- Temporary server errors (500, 502, 503, 504)

This module provides a resilient HTTP client that automatically:
1. Retries failed requests (up to 3 times)
2. Waits between retries (exponential backoff: 0.2s, 0.5s, 1.2s)
3. Respects timeouts to avoid hanging forever

Usage:
    from agent.retry import request_with_retry
    
    # GET request
    data = await request_with_retry("GET", "https://api.example.com/data")
    
    # POST request with JSON body
    data = await request_with_retry("POST", url, json={"key": "value"})
"""

import asyncio
import httpx
from typing import Any

# =============================================================================
# CONFIGURATION
# =============================================================================

# HTTP status codes that should trigger a retry
# 429 = Rate limited (too many requests)
# 500 = Internal server error
# 502 = Bad gateway
# 503 = Service unavailable
# 504 = Gateway timeout
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

# Delays between retries (exponential backoff)
# First retry after 0.2s, second after 0.5s, third after 1.2s
RETRY_DELAYS = [0.2, 0.5, 1.2]

# Default timeout for HTTP requests (seconds)
DEFAULT_TIMEOUT = 10.0


# =============================================================================
# MAIN FUNCTION
# =============================================================================

async def request_with_retry(
    method: str,
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    json: dict | None = None,
    timeout: float = DEFAULT_TIMEOUT
) -> dict[str, Any]:
    """
    Make an HTTP request with automatic retry on failure.
    
    Args:
        method: HTTP method ("GET", "POST", etc.)
        url: The URL to request
        params: Query parameters (for GET requests)
        headers: HTTP headers (e.g., Authorization)
        json: JSON body (for POST requests)
        timeout: Request timeout in seconds (default: 10.0)
        
    Returns:
        Parsed JSON response as a dictionary
        
    Raises:
        RuntimeError: If all retries fail
        httpx.HTTPStatusError: If server returns non-retryable error (e.g., 400, 404)
        
    Example:
        >>> data = await request_with_retry("GET", "https://api.example.com/data")
        >>> print(data["result"])
    """
    
    # Track the last error for the final exception message
    last_error: Exception | None = None
    
    # Calculate total attempts: initial + retries
    # len(RETRY_DELAYS) = 3, so total attempts = 4 (1 + 3)
    total_attempts = len(RETRY_DELAYS) + 1
    
    for attempt in range(total_attempts):
        try:
            # Create a new client for each attempt
            # timeout is set per-request to avoid hanging
            async with httpx.AsyncClient(timeout=timeout) as client:
                
                # Make the actual HTTP request
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    json=json
                )
                
                # Check if we got a retryable status code
                if response.status_code in RETRY_STATUS_CODES:
                    # Log the retry (in production, use proper logging)
                    print(f"[retry] Attempt {attempt + 1}: Got {response.status_code}, will retry...")
                    raise RuntimeError(f"Retryable HTTP status: {response.status_code}")
                
                # Raise exception for other error status codes (4xx except 429)
                # This will NOT retry on 400 Bad Request, 404 Not Found, etc.
                response.raise_for_status()
                
                # Success! Parse and return JSON response
                return response.json()
                
        except Exception as e:
            # Store the error for potential final exception
            last_error = e
            
            # Check if we have more retries left
            if attempt < len(RETRY_DELAYS):
                # Wait before retrying (exponential backoff)
                delay = RETRY_DELAYS[attempt]
                print(f"[retry] Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                # No more retries - give up and raise the last error
                print(f"[retry] All {total_attempts} attempts failed. Giving up.")
                raise last_error


# =============================================================================
# CONVENIENCE FUNCTIONS (optional, for cleaner code)
# =============================================================================

async def get_json(url: str, params: dict | None = None, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """
    Convenience function for GET requests that return JSON.
    
    Args:
        url: The URL to request
        params: Query parameters
        timeout: Request timeout in seconds
        
    Returns:
        Parsed JSON response
    """
    return await request_with_retry("GET", url, params=params, timeout=timeout)


async def post_json(
    url: str,
    json: dict,
    headers: dict | None = None,
    timeout: float = DEFAULT_TIMEOUT
) -> dict:
    """
    Convenience function for POST requests with JSON body.
    
    Args:
        url: The URL to request
        json: JSON body to send
        headers: HTTP headers
        timeout: Request timeout in seconds
        
    Returns:
        Parsed JSON response
    """
    return await request_with_retry("POST", url, json=json, headers=headers, timeout=timeout)
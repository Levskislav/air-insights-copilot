"""
agent/http_client.py
====================
Shared HTTP client with connection pooling.

This module provides a singleton AsyncClient that reuses connections
for better performance. Instead of creating a new client for each request,
we maintain a single client with connection pooling.

Benefits:
1. Connection reuse (HTTP keep-alive)
2. Better performance (no TCP handshake overhead)
3. Proper resource management
4. Configurable connection limits
"""

import httpx
from typing import Optional

from agent.config import DEFAULT_HTTP_TIMEOUT_SECONDS
from agent.logging_config import log_debug


# =============================================================================
# CONFIGURATION
# =============================================================================

# Connection pool limits
MAX_KEEPALIVE_CONNECTIONS = 20  # Max idle connections to keep
MAX_CONNECTIONS = 100           # Max total connections


# =============================================================================
# SINGLETON CLIENT
# =============================================================================

_client: Optional[httpx.AsyncClient] = None


async def get_client() -> httpx.AsyncClient:
    """
    Get or create the shared HTTP client.
    
    This function returns a singleton AsyncClient with connection pooling.
    The client is created lazily on first use.
    
    Returns:
        The shared httpx.AsyncClient instance
        
    Example:
        >>> client = await get_client()
        >>> response = await client.get("https://api.example.com/data")
    """
    global _client
    
    if _client is None:
        log_debug("Creating shared HTTP client")
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(DEFAULT_HTTP_TIMEOUT_SECONDS),
            limits=httpx.Limits(
                max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
                max_connections=MAX_CONNECTIONS
            ),
            # Follow redirects by default
            follow_redirects=True,
        )
    
    return _client


async def close_client() -> None:
    """
    Close the shared HTTP client.
    
    Should be called during application shutdown to properly
    release all connections.
    
    Example:
        >>> await close_client()  # Call in shutdown handler
    """
    global _client
    
    if _client is not None:
        log_debug("Closing shared HTTP client")
        await _client.aclose()
        _client = None


# =============================================================================
# LIFESPAN INTEGRATION
# =============================================================================

async def startup() -> None:
    """
    Initialize the HTTP client on application startup.
    
    Call this from your FastAPI lifespan handler.
    """
    await get_client()
    log_debug("HTTP client initialized")


async def shutdown() -> None:
    """
    Cleanup the HTTP client on application shutdown.
    
    Call this from your FastAPI lifespan handler.
    """
    await close_client()
    log_debug("HTTP client closed")

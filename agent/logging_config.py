"""
agent/logging_config.py
=======================
Structured logging configuration for OutdoorMate.

Features:
- Request ID tracking
- Latency measurement
- Colored console output
- JSON format for production
"""

import logging
import sys
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable

# =============================================================================
# CONTEXT VARIABLES
# =============================================================================

# Request ID for tracking across async calls
request_id_var: ContextVar[str] = ContextVar("request_id", default="no-request")


# =============================================================================
# CUSTOM FORMATTER
# =============================================================================

class ColoredFormatter(logging.Formatter):
    """Formatter with colors for console output."""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        # Add request_id to record
        record.request_id = request_id_var.get()
        
        # Add color
        color = self.COLORS.get(record.levelname, "")
        record.levelname_colored = f"{color}{record.levelname}{self.RESET}"
        
        return super().format(record)


# =============================================================================
# LOGGER SETUP
# =============================================================================

def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure and return the main application logger.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("outdoormate")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Format: [LEVEL] [request_id] message
    formatter = ColoredFormatter(
        fmt="%(levelname_colored)s [%(request_id)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
logger = setup_logging()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())[:8]


def set_request_id(request_id: str | None = None) -> str:
    """Set the request ID for the current context."""
    rid = request_id or generate_request_id()
    request_id_var.set(rid)
    return rid


def get_request_id() -> str:
    """Get the current request ID."""
    return request_id_var.get()


# =============================================================================
# TIMING DECORATOR
# =============================================================================

def log_timing(operation: str) -> Callable:
    """
    Decorator to log execution time of async functions.
    
    Args:
        operation: Name of the operation being timed
        
    Example:
        @log_timing("fetch_weather")
        async def fetch_weather(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.info(f"{operation} completed in {elapsed:.1f}ms")
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(f"{operation} failed after {elapsed:.1f}ms: {e}")
                raise
        return wrapper
    return decorator


# =============================================================================
# LOG HELPERS
# =============================================================================

def log_request_start(endpoint: str, params: dict) -> None:
    """Log the start of a request."""
    logger.info(f"→ {endpoint} | params={params}")


def log_request_end(endpoint: str, status: int, latency_ms: float) -> None:
    """Log the end of a request."""
    if status < 400:
        logger.info(f"← {endpoint} | status={status} | {latency_ms:.1f}ms")
    else:
        logger.warning(f"← {endpoint} | status={status} | {latency_ms:.1f}ms")


def log_cache_hit(key: str) -> None:
    """Log a cache hit."""
    logger.debug(f"CACHE HIT: {key}")


def log_cache_miss(key: str) -> None:
    """Log a cache miss."""
    logger.debug(f"CACHE MISS: {key}")


def log_external_call(service: str, endpoint: str) -> None:
    """Log an external API call."""
    logger.debug(f"→ External: {service} {endpoint}")


def log_llm_call(model: str, tokens: int | None = None) -> None:
    """Log an LLM call."""
    if tokens:
        logger.info(f"LLM: {model} | {tokens} tokens")
    else:
        logger.info(f"LLM: {model}")


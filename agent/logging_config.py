"""
agent/logging_config.py
=======================
Structured logging configuration for Air & Insights Copilot.

Features:
- JSON logs for production (LOG_FORMAT=json)
- Colored console logs for development
- Configurable log level via LOG_LEVEL env var
- Helper functions for structured logging
"""

import logging
import sys
import json
import os
from datetime import datetime, timezone
from typing import Any


# =============================================================================
# CONFIGURATION
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # "json" for production


# =============================================================================
# FORMATTERS
# =============================================================================

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging in production."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
            
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for readable console output."""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green  
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname:8}{self.RESET}"
        return super().format(record)


# =============================================================================
# LOGGER SETUP
# =============================================================================

def get_logger(name: str = "air_insights") -> logging.Logger:
    """
    Get or create a configured logger.
    
    Args:
        name: Logger name (default: "air_insights")
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already done
    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, LOG_LEVEL))
        
        if LOG_FORMAT == "json":
            handler.setFormatter(JsonFormatter())
        else:
            # Use ASCII-safe separator for Windows compatibility
            handler.setFormatter(ColoredFormatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%H:%M:%S"
            ))
        
        logger.addHandler(handler)
        logger.propagate = False
    
    return logger


# Create default logger
logger = get_logger()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_info(message: str, **context: Any) -> None:
    """Log info message with optional context."""
    if context:
        ctx_str = " | ".join(f"{k}={v}" for k, v in context.items())
        logger.info(f"{message} | {ctx_str}")
    else:
        logger.info(message)


def log_debug(message: str, **context: Any) -> None:
    """Log debug message with optional context."""
    if context:
        ctx_str = " | ".join(f"{k}={v}" for k, v in context.items())
        logger.debug(f"{message} | {ctx_str}")
    else:
        logger.debug(message)


def log_warning(message: str, **context: Any) -> None:
    """Log warning message with optional context."""
    if context:
        ctx_str = " | ".join(f"{k}={v}" for k, v in context.items())
        logger.warning(f"{message} | {ctx_str}")
    else:
        logger.warning(message)


def log_error(message: str, **context: Any) -> None:
    """Log error message with optional context."""
    if context:
        ctx_str = " | ".join(f"{k}={v}" for k, v in context.items())
        logger.error(f"{message} | {ctx_str}")
    else:
        logger.error(message)


def log_api_call(service: str, endpoint: str, success: bool, duration_ms: float, **extra) -> None:
    """Log external API calls."""
    status = "✓" if success else "✗"
    level = "info" if success else "warning"
    msg = f"API {status} {service}/{endpoint} | duration_ms={duration_ms:.1f}"
    if extra:
        msg += " | " + " | ".join(f"{k}={v}" for k, v in extra.items())
    getattr(logger, level)(msg)


def log_cache(action: str, key: str, hit: bool = None) -> None:
    """Log cache operations."""
    if action == "check":
        status = "HIT ✓" if hit else "MISS"
        logger.debug(f"Cache {status} | key={key[:40]}...")
    else:
        logger.debug(f"Cache {action.upper()} | key={key[:40]}...")

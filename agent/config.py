"""
agent/config.py
===============
Centralized configuration for Air & Insights Copilot.

All configuration is loaded from environment variables with sensible defaults.
This is the single source of truth for app settings.
"""

import os
from dataclasses import dataclass


# =============================================================================
# VERSION & CONSTANTS
# =============================================================================

VERSION = "1.0.0"

# API limits
MAX_FORECAST_HOURS = 72
MIN_FORECAST_HOURS = 1

# Cache settings
DEFAULT_CACHE_TTL_SECONDS = 600  # 10 minutes
DEFAULT_CACHE_MAX_SIZE = 1024

# HTTP settings
DEFAULT_HTTP_TIMEOUT_SECONDS = 10.0
DEFAULT_LLM_TIMEOUT_SECONDS = 15.0

# Coordinate precision (4 decimal places = ~11m accuracy)
COORDINATE_PRECISION = 4

# Air quality thresholds (WHO guidelines)
PM25_GOOD_THRESHOLD = 15.0  # μg/m³
PM25_MODERATE_THRESHOLD = 35.0  # μg/m³

# Temperature thresholds (Celsius)
TEMP_FREEZING = -5
TEMP_COLD = 5
TEMP_COOL = 15
TEMP_HOT = 25


# =============================================================================
# CONFIGURATION CLASS
# =============================================================================

@dataclass
class Config:
    """Application configuration loaded from environment."""
    
    # App info
    version: str = VERSION
    app_name: str = "Air & Insights Copilot"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS - comma-separated list of origins, or "*" for dev
    cors_origins: list[str] = None
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    # API Keys (validated on startup)
    github_token: str = None
    google_api_key: str = None
    nasa_api_key: str = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "text"  # "json" for production
    
    def __post_init__(self):
        """Load values from environment."""
        self.host = os.getenv("HOST", self.host)
        self.port = int(os.getenv("PORT", self.port))
        
        # CORS origins
        cors_env = os.getenv("CORS_ORIGINS", "*")
        if cors_env == "*":
            self.cors_origins = ["*"]
        else:
            self.cors_origins = [o.strip() for o in cors_env.split(",")]
        
        # Rate limiting
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", self.rate_limit_per_minute))
        
        # API Keys
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.nasa_api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", self.log_level).upper()
        self.log_format = os.getenv("LOG_FORMAT", self.log_format)
    
    def validate_required_secrets(self) -> list[str]:
        """
        Check if required secrets are configured.
        
        Returns:
            List of missing secret names (empty if all present)
        """
        missing = []
        
        if not self.github_token:
            missing.append("GITHUB_TOKEN")
        
        # Google API key is optional (geocoding will fail gracefully)
        # NASA API key has a default (DEMO_KEY)
        
        return missing


# Global config instance
config = Config()


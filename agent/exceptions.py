"""
agent/exceptions.py
===================
Custom exception classes for Air & Insights Copilot.

Using custom exceptions provides:
1. Clear error categorization
2. Appropriate HTTP status code mapping
3. Better error messages for users
4. Easier debugging and logging
"""


class AirInsightsError(Exception):
    """Base exception for all Air & Insights errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AirInsightsError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class GeocodingError(AirInsightsError):
    """Raised when geocoding fails."""
    
    def __init__(self, place_name: str, reason: str = "Location not found"):
        message = f"Could not geocode '{place_name}': {reason}"
        super().__init__(message, status_code=400)
        self.place_name = place_name


class ExternalAPIError(AirInsightsError):
    """Raised when an external API call fails."""
    
    def __init__(self, service: str, reason: str = "Service unavailable"):
        message = f"External API error ({service}): {reason}"
        super().__init__(message, status_code=502)
        self.service = service


class ConfigurationError(AirInsightsError):
    """Raised when required configuration is missing."""
    
    def __init__(self, missing_key: str):
        message = f"Missing required configuration: {missing_key}"
        super().__init__(message, status_code=500)
        self.missing_key = missing_key


class RateLimitError(AirInsightsError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int = 60):
        message = f"Rate limit exceeded. Try again in {retry_after} seconds."
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


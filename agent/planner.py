"""
agent/planner.py
================
Agent planning module - decides which tools to use.

Currently a simple rule-based planner that always fetches all data.
The structure allows for future extensions like:
- Conditional planning based on user query
- LLM-based planning
- Seasonal adjustments (e.g., skip snow in summer)
"""

from dataclasses import dataclass

from agent.logging_config import log_debug


# =============================================================================
# PLAN DATA STRUCTURES
# =============================================================================

@dataclass
class AnalyzePlan:
    """
    Execution plan for the /analyze endpoint.
    
    Attributes:
        need_air: Whether to fetch air quality data
        need_weather: Whether to fetch weather data
        air_variables: Which air quality variables to request
        weather_variables: Which weather variables to request
    """
    need_air: bool = True
    need_weather: bool = True
    air_variables: list[str] = None
    weather_variables: list[str] = None
    
    def __post_init__(self):
        """Set default variables if not provided."""
        if self.air_variables is None:
            self.air_variables = ["pm2_5", "pm10"]
        if self.weather_variables is None:
            self.weather_variables = ["temperature_2m"]


# =============================================================================
# PLANNING FUNCTIONS
# =============================================================================

def plan_for_analyze(lat: float, lon: float, hours: int) -> AnalyzePlan:
    """
    Create an execution plan for the /analyze request.
    
    This function decides:
    - Which external APIs to call
    - Which variables to fetch from each API
    
    Args:
        lat: Latitude (not used yet, but available for location-based decisions)
        lon: Longitude (not used yet)
        hours: Number of hours (not used yet)
        
    Returns:
        AnalyzePlan with tool selection decisions
        
    Example:
        >>> plan = plan_for_analyze(42.6977, 23.3219, 6)
        >>> if plan.need_air:
        ...     air_data = await fetch_air_quality(...)
        
    Future improvements:
        - Skip weather if user only asks about air quality
        - Add UV index for sunny locations
        - Add pollen data for spring months
        - Use LLM to decide based on user's question
    """
    # For now, always fetch both air quality and weather
    # This is the simplest approach that covers our use case
    
    plan = AnalyzePlan(
        need_air=True,
        need_weather=True,
        air_variables=["pm2_5", "pm10"],
        weather_variables=["temperature_2m"]
    )
    
    log_debug("Execution plan created", lat=lat, lon=lon, hours=hours,
              need_air=plan.need_air, need_weather=plan.need_weather)
    
    return plan


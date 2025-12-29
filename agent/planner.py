"""
agent/planner.py
================
Agent planning module - decides which tools to use.

The planner gives our system an "agentic" feel. Instead of hardcoding
which APIs to call, we ask the planner "what do we need for this request?"

For now, this is a simple rule-based planner:
- /analyze always needs air quality + weather data

In the future, this could be:
- LLM-based planning (ask GPT what tools to use)
- Conditional planning (skip weather if user only asks about air)
- Multi-step planning (fetch → validate → compute → reason)
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


# =============================================================================
# FUTURE: LLM-BASED PLANNING
# =============================================================================

# In a more advanced system, we could use an LLM to decide the plan:
#
# async def plan_with_llm(user_question: str) -> AnalyzePlan:
#     """
#     Use LLM to decide which tools to use based on user's question.
#     
#     Example:
#         "Is the air quality good?" -> need_air=True, need_weather=False
#         "What's the temperature?" -> need_air=False, need_weather=True
#         "Should I go running?" -> need_air=True, need_weather=True
#     """
#     # This would call GitHub Models with a prompt like:
#     # "Based on this question, which data do we need: air quality, weather, or both?"
#     pass
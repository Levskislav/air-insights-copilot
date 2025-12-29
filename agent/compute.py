"""
agent/compute.py
================
Statistical computations for weather and air quality data.

This module provides safe computation functions that handle
missing values (None) gracefully. This is important because
Open-Meteo may return null for some hours when data is unavailable.

Key function:
- safe_avg(): Computes average while ignoring None values
"""

from typing import Sequence


# =============================================================================
# SAFE AVERAGE FUNCTION
# =============================================================================

def safe_avg(values: Sequence[float | None] | None) -> float | None:
    """
    Compute the average of a list, safely ignoring None values.
    
    This function handles cases where:
    - The input list is None
    - The input list is empty
    - The list contains some None values
    - The list contains ALL None values
    
    Args:
        values: A list of numbers that may contain None values
        
    Returns:
        The average of non-None values, or None if no valid values exist
        
    Examples:
        >>> safe_avg([1.0, 2.0, 3.0])
        2.0
        
        >>> safe_avg([1.0, None, 3.0])  # None is ignored
        2.0
        
        >>> safe_avg([None, None])  # All None
        None
        
        >>> safe_avg([])  # Empty list
        None
        
        >>> safe_avg(None)  # None input
        None
    """
    # Handle None or empty input
    if not values:
        return None
    
    # Filter out None values, keeping only valid numbers
    valid_numbers = [v for v in values if v is not None]
    
    # If no valid numbers remain, return None
    if not valid_numbers:
        return None
    
    # Compute and return the average
    return sum(valid_numbers) / len(valid_numbers)


# =============================================================================
# ADDITIONAL STATISTICS (optional, for future use)
# =============================================================================

def safe_min(values: Sequence[float | None] | None) -> float | None:
    """
    Find the minimum value, ignoring None values.
    
    Args:
        values: A list of numbers that may contain None values
        
    Returns:
        The minimum value, or None if no valid values exist
    """
    if not values:
        return None
    
    valid_numbers = [v for v in values if v is not None]
    
    if not valid_numbers:
        return None
    
    return min(valid_numbers)


def safe_max(values: Sequence[float | None] | None) -> float | None:
    """
    Find the maximum value, ignoring None values.
    
    Args:
        values: A list of numbers that may contain None values
        
    Returns:
        The maximum value, or None if no valid values exist
    """
    if not values:
        return None
    
    valid_numbers = [v for v in values if v is not None]
    
    if not valid_numbers:
        return None
    
    return max(valid_numbers)


def round_or_none(value: float | None, decimals: int = 2) -> float | None:
    """
    Round a value to specified decimals, or return None if input is None.
    
    Args:
        value: The value to round (may be None)
        decimals: Number of decimal places (default: 2)
        
    Returns:
        Rounded value, or None if input is None
        
    Example:
        >>> round_or_none(12.3456, 2)
        12.35
        
        >>> round_or_none(None, 2)
        None
    """
    if value is None:
        return None
    return round(value, decimals)
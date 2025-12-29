"""
tests/test_compute.py
=====================
Unit tests for agent/compute.py - statistical computations.
"""

import pytest
from agent.compute import safe_avg, safe_min, safe_max, round_or_none


class TestSafeAvg:
    """Tests for safe_avg function."""
    
    def test_basic_average(self):
        """Basic average of valid numbers."""
        assert safe_avg([1.0, 2.0, 3.0]) == 2.0
        assert safe_avg([10.0, 20.0]) == 15.0
    
    def test_single_value(self):
        """Single value returns itself."""
        assert safe_avg([5.0]) == 5.0
    
    def test_with_none_values(self):
        """None values should be ignored."""
        assert safe_avg([1.0, None, 3.0]) == 2.0
        assert safe_avg([None, 2.0, None, 4.0]) == 3.0
    
    def test_all_none(self):
        """All None values should return None."""
        assert safe_avg([None, None, None]) is None
    
    def test_empty_list(self):
        """Empty list should return None."""
        assert safe_avg([]) is None
    
    def test_none_input(self):
        """None input should return None."""
        assert safe_avg(None) is None


class TestSafeMin:
    """Tests for safe_min function."""
    
    def test_basic_min(self):
        """Basic minimum of valid numbers."""
        assert safe_min([3.0, 1.0, 2.0]) == 1.0
    
    def test_with_none(self):
        """None values should be ignored."""
        assert safe_min([None, 5.0, None, 3.0]) == 3.0
    
    def test_all_none(self):
        """All None should return None."""
        assert safe_min([None, None]) is None
    
    def test_empty_list(self):
        """Empty list should return None."""
        assert safe_min([]) is None


class TestSafeMax:
    """Tests for safe_max function."""
    
    def test_basic_max(self):
        """Basic maximum of valid numbers."""
        assert safe_max([1.0, 3.0, 2.0]) == 3.0
    
    def test_with_none(self):
        """None values should be ignored."""
        assert safe_max([None, 5.0, None, 3.0]) == 5.0
    
    def test_all_none(self):
        """All None should return None."""
        assert safe_max([None, None]) is None


class TestRoundOrNone:
    """Tests for round_or_none function."""
    
    def test_basic_rounding(self):
        """Basic rounding to 2 decimals."""
        assert round_or_none(12.3456, 2) == 12.35
    
    def test_none_input(self):
        """None input should return None."""
        assert round_or_none(None, 2) is None
    
    def test_default_decimals(self):
        """Default should be 2 decimals."""
        assert round_or_none(12.3456) == 12.35


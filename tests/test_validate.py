"""
tests/test_validate.py
======================
Unit tests for agent/validate.py - input validation and data quality.
"""

import pytest
from agent.validate import (
    validate_lat_lon,
    validate_hours,
    validate_open_meteo_payload,
    QualityFlags,
    _check_sparseness,
    _get_hourly_array,
)


class TestValidateLatLon:
    """Tests for validate_lat_lon function."""
    
    def test_valid_coordinates(self):
        """Valid coordinates should not raise."""
        validate_lat_lon(42.6977, 23.3219)  # Sofia
        validate_lat_lon(0.0, 0.0)  # Equator/Prime Meridian
        validate_lat_lon(-33.8688, 151.2093)  # Sydney
    
    def test_boundary_values(self):
        """Boundary values should be valid."""
        validate_lat_lon(90.0, 180.0)  # Max values
        validate_lat_lon(-90.0, -180.0)  # Min values
    
    def test_invalid_latitude_high(self):
        """Latitude > 90 should raise ValueError."""
        with pytest.raises(ValueError, match="Latitude"):
            validate_lat_lon(91.0, 0.0)
    
    def test_invalid_latitude_low(self):
        """Latitude < -90 should raise ValueError."""
        with pytest.raises(ValueError, match="Latitude"):
            validate_lat_lon(-91.0, 0.0)
    
    def test_invalid_longitude_high(self):
        """Longitude > 180 should raise ValueError."""
        with pytest.raises(ValueError, match="Longitude"):
            validate_lat_lon(0.0, 181.0)
    
    def test_invalid_longitude_low(self):
        """Longitude < -180 should raise ValueError."""
        with pytest.raises(ValueError, match="Longitude"):
            validate_lat_lon(0.0, -181.0)


class TestValidateHours:
    """Tests for validate_hours function."""
    
    def test_valid_hours(self):
        """Valid hours should not raise."""
        validate_hours(1)
        validate_hours(6)
        validate_hours(24)
        validate_hours(168)
    
    def test_invalid_hours_low(self):
        """Hours < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="Hours"):
            validate_hours(0)
    
    def test_invalid_hours_high(self):
        """Hours > 168 should raise ValueError."""
        with pytest.raises(ValueError, match="Hours"):
            validate_hours(169)
    
    def test_invalid_hours_negative(self):
        """Negative hours should raise ValueError."""
        with pytest.raises(ValueError, match="Hours"):
            validate_hours(-5)


class TestCheckSparseness:
    """Tests for _check_sparseness helper."""
    
    def test_full_data(self):
        """Full data is not sparse."""
        assert _check_sparseness([1.0, 2.0, 3.0]) is False
    
    def test_empty_list(self):
        """Empty list is sparse."""
        assert _check_sparseness([]) is True
    
    def test_none_input(self):
        """None input is sparse."""
        assert _check_sparseness(None) is True
    
    def test_all_none_values(self):
        """All None values is sparse."""
        assert _check_sparseness([None, None, None]) is True
    
    def test_half_none(self):
        """50% valid is exactly at threshold (NOT sparse)."""
        # Code uses < threshold, so 50% valid is NOT sparse
        assert _check_sparseness([1.0, None]) is False
    
    def test_below_threshold(self):
        """Below 50% valid IS sparse."""
        assert _check_sparseness([1.0, None, None, None]) is True
    
    def test_mostly_valid(self):
        """Mostly valid data is not sparse."""
        assert _check_sparseness([1.0, 2.0, 3.0, None]) is False


class TestGetHourlyArray:
    """Tests for _get_hourly_array helper."""
    
    def test_valid_payload(self):
        """Extract array from valid payload."""
        payload = {"hourly": {"pm2_5": [10.0, 20.0, 30.0]}}
        result = _get_hourly_array(payload, "pm2_5")
        assert result == [10.0, 20.0, 30.0]
    
    def test_missing_key(self):
        """Missing key returns None."""
        payload = {"hourly": {"pm2_5": [10.0]}}
        result = _get_hourly_array(payload, "pm10")
        assert result is None
    
    def test_none_payload(self):
        """None payload returns None."""
        assert _get_hourly_array(None, "pm2_5") is None
    
    def test_no_hourly_section(self):
        """Payload without hourly returns None."""
        assert _get_hourly_array({}, "pm2_5") is None


class TestQualityFlags:
    """Tests for QualityFlags dataclass."""
    
    def test_default_no_issues(self):
        """Default flags have no issues."""
        flags = QualityFlags()
        assert flags.has_issues() is False
    
    def test_sparse_air_is_issue(self):
        """Sparse air data is an issue."""
        flags = QualityFlags(sparse_air=True)
        assert flags.has_issues() is True
    
    def test_sparse_weather_is_issue(self):
        """Sparse weather data is an issue."""
        flags = QualityFlags(sparse_weather=True)
        assert flags.has_issues() is True
    
    def test_missing_fields_is_issue(self):
        """Missing fields is an issue."""
        flags = QualityFlags(missing_fields=["pm2_5"])
        assert flags.has_issues() is True


class TestValidateOpenMeteoPayload:
    """Tests for validate_open_meteo_payload function."""
    
    def test_complete_data(self):
        """Complete data with no issues."""
        air_json = {
            "hourly": {
                "pm2_5": [10.0, 20.0, 30.0],
                "pm10": [15.0, 25.0, 35.0],
            }
        }
        wx_json = {
            "hourly": {
                "temperature_2m": [20.0, 21.0, 22.0],
            }
        }
        
        data, flags = validate_open_meteo_payload(air_json, wx_json, 3)
        
        assert data["pm25"] == [10.0, 20.0, 30.0]
        assert data["pm10"] == [15.0, 25.0, 35.0]
        assert data["temp"] == [20.0, 21.0, 22.0]
        assert flags.has_issues() is False
    
    def test_slicing_to_hours(self):
        """Data is sliced to requested hours."""
        air_json = {
            "hourly": {
                "pm2_5": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "pm10": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            }
        }
        wx_json = {
            "hourly": {
                "temperature_2m": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            }
        }
        
        data, flags = validate_open_meteo_payload(air_json, wx_json, 3)
        
        assert len(data["pm25"]) == 3
        assert len(data["pm10"]) == 3
        assert len(data["temp"]) == 3
    
    def test_no_air_data(self):
        """No air data sets sparse_air flag."""
        wx_json = {
            "hourly": {
                "temperature_2m": [20.0, 21.0, 22.0],
            }
        }
        
        data, flags = validate_open_meteo_payload(None, wx_json, 3)
        
        assert flags.sparse_air is True
        assert "pm2_5" in flags.missing_fields
        assert "pm10" in flags.missing_fields
    
    def test_no_weather_data(self):
        """No weather data sets sparse_weather flag."""
        air_json = {
            "hourly": {
                "pm2_5": [10.0, 20.0, 30.0],
                "pm10": [15.0, 25.0, 35.0],
            }
        }
        
        data, flags = validate_open_meteo_payload(air_json, None, 3)
        
        assert flags.sparse_weather is True
        assert "temperature_2m" in flags.missing_fields


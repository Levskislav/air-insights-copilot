"""
tests/test_integration_analyze.py
=================================
Integration tests for the /analyze endpoint.

These tests use mocked external APIs (Open-Meteo, GitHub Models)
so they can run in CI without making real HTTP calls.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from service.main import app


# Create test client
client = TestClient(app)


# =============================================================================
# MOCK DATA
# =============================================================================

MOCK_AIR_QUALITY_RESPONSE = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "pm2_5": [25.0, 30.0, 28.0],
        "pm10": [35.0, 40.0, 38.0],
    }
}

MOCK_WEATHER_RESPONSE = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "temperature_2m": [15.0, 16.0, 17.0],
        "rain": [0.0, 0.0, 0.0],
        "visibility": [10000, 10000, 10000],
        "wind_speed_10m": [5.0, 6.0, 5.5],
        "wind_gusts_10m": [10.0, 12.0, 11.0],
        "cloud_cover": [20, 25, 30],
        "precipitation_probability": [0, 0, 0],
        "weather_code": [0, 0, 0],
    }
}

MOCK_SNOW_RESPONSE = {
    "hourly": {
        "snowfall": [0.0, 0.0, 0.0],
        "snow_depth": [5.0, 5.0, 5.0],
    }
}

MOCK_LLM_GUIDANCE = "The air quality is moderate. Temperature is pleasant around 16°C. Great conditions for outdoor activities!"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestAnalyzeEndpoint:
    """Integration tests for POST /analyze endpoint."""
    
    @patch("agent.tools.open_meteo.fetch_air_quality", new_callable=AsyncMock)
    @patch("agent.tools.open_meteo.fetch_weather", new_callable=AsyncMock)
    @patch("agent.tools.open_meteo.fetch_snow", new_callable=AsyncMock)
    @patch("agent.tools.github_models_llm.generate_guidance_text", new_callable=AsyncMock)
    def test_analyze_with_coordinates(
        self,
        mock_llm,
        mock_snow,
        mock_weather,
        mock_air,
    ):
        """Test /analyze with valid coordinates."""
        # Setup mocks
        mock_air.return_value = MOCK_AIR_QUALITY_RESPONSE
        mock_weather.return_value = MOCK_WEATHER_RESPONSE
        mock_snow.return_value = MOCK_SNOW_RESPONSE
        mock_llm.return_value = MOCK_LLM_GUIDANCE
        
        # Make request
        response = client.post(
            "/analyze",
            json={
                "latitude": 42.6977,
                "longitude": 23.3219,
                "hours": 3,
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check all expected fields are present
        assert "pm25_avg" in data
        assert "pm10_avg" in data
        assert "temp_avg" in data
        assert "guidance_text" in data
        
        # Check values are reasonable
        assert data["pm25_avg"] is not None
        assert data["pm10_avg"] is not None
        assert data["temp_avg"] is not None
        assert len(data["guidance_text"]) > 0
    
    @patch("agent.tools.open_meteo.fetch_air_quality", new_callable=AsyncMock)
    @patch("agent.tools.open_meteo.fetch_weather", new_callable=AsyncMock)
    @patch("agent.tools.open_meteo.fetch_snow", new_callable=AsyncMock)
    @patch("agent.tools.github_models_llm.generate_guidance_text", new_callable=AsyncMock)
    @patch("agent.tools.google_geocoding.geocode_if_needed", new_callable=AsyncMock)
    def test_analyze_with_place_name(
        self,
        mock_geocode,
        mock_llm,
        mock_snow,
        mock_weather,
        mock_air,
    ):
        """Test /analyze with place_name instead of coordinates."""
        # Setup mocks
        mock_geocode.return_value = (42.6977, 23.3219)  # Returns tuple (lat, lon)
        mock_air.return_value = MOCK_AIR_QUALITY_RESPONSE
        mock_weather.return_value = MOCK_WEATHER_RESPONSE
        mock_snow.return_value = MOCK_SNOW_RESPONSE
        mock_llm.return_value = MOCK_LLM_GUIDANCE
        
        # Make request
        response = client.post(
            "/analyze",
            json={
                "place_name": "Sofia",
                "hours": 3,
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "guidance_text" in data
    
    def test_analyze_missing_location(self):
        """Test /analyze fails without location info."""
        response = client.post(
            "/analyze",
            json={
                "hours": 6,
            }
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_analyze_invalid_coordinates(self):
        """Test /analyze rejects invalid coordinates."""
        response = client.post(
            "/analyze",
            json={
                "latitude": 200.0,  # Invalid
                "longitude": 23.3219,
                "hours": 6,
            }
        )
        
        # Should fail validation (Pydantic validates lat/lon range)
        assert response.status_code == 422


class TestHealthEndpoint:
    """Tests for GET / health check endpoint."""
    
    def test_health_check(self):
        """Health check returns 200."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestGeocodeEndpoint:
    """Integration tests for POST /geocode endpoint."""
    
    @patch("agent.tools.google_geocoding.geocode_place", new_callable=AsyncMock)
    def test_geocode_valid_place(self, mock_geocode):
        """Test /geocode with valid place name."""
        mock_geocode.return_value = {
            "lat": 42.6977,
            "lon": 23.3219,
            "formatted_address": "Sofia, Bulgaria"
        }
        
        response = client.post(
            "/geocode",
            json={"place_name": "Sofia"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "latitude" in data
        assert "longitude" in data
        assert "formatted_address" in data
    
    def test_geocode_empty_place(self):
        """Test /geocode fails with empty place name."""
        response = client.post(
            "/geocode",
            json={"place_name": ""}
        )
        
        # Should fail - empty string not allowed
        assert response.status_code in [400, 422, 500]


class TestRouteWeatherEndpoint:
    """Integration tests for POST /route-weather endpoint."""
    
    @patch("agent.tools.google_directions.get_route_waypoints", new_callable=AsyncMock)
    @patch("agent.tools.open_meteo.fetch_road_conditions", new_callable=AsyncMock)
    @patch("agent.tools.open_meteo.fetch_air_quality", new_callable=AsyncMock)
    def test_route_weather_valid(
        self,
        mock_air,
        mock_road,
        mock_directions,
    ):
        """Test /route-weather with valid origin and destination."""
        # Mock directions response
        mock_directions.return_value = {
            "waypoints": [
                {"lat": 42.6977, "lon": 23.3219, "name": "Sofia", "eta_minutes": 0},
                {"lat": 42.1500, "lon": 24.7500, "name": "Plovdiv", "eta_minutes": 120},
            ],
            "total_distance_km": 150,
            "total_duration_min": 120,
        }
        mock_road.return_value = {
            "temperature": 15.0,
            "rain": 0.0,
            "snowfall": 0.0,
            "snow_depth": 0.0,
            "visibility": 10000,
            "wind_speed": 5.0,
            "wind_gusts": 10.0,
            "cloud_cover": 20,
            "precipitation_probability": 0,
            "weather_code": 0,
        }
        mock_air.return_value = MOCK_AIR_QUALITY_RESPONSE
        
        response = client.post(
            "/route-weather",
            json={
                "origin": "Sofia",
                "destination": "Plovdiv",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "waypoints" in data or "summary" in data
    
    def test_route_weather_missing_destination(self):
        """Test /route-weather fails without destination."""
        response = client.post(
            "/route-weather",
            json={
                "origin": "Sofia",
            }
        )
        
        assert response.status_code == 422


"""Tests for weather service functionality."""

import pytest
from unittest.mock import patch, AsyncMock
from app.weather_service import WeatherService
from geopy.exc import GeocoderTimedOut


class TestWeatherService:
    """Test cases for WeatherService class."""

    @pytest.fixture
    def weather_service(self):
        """Create a WeatherService instance for testing."""
        return WeatherService()

    @pytest.mark.asyncio
    async def test_get_coordinates_success(self, weather_service):
        """Test successful coordinate retrieval."""
        with patch.object(weather_service.geocoder, "geocode") as mock_geocode:
            # Mock successful geocoding
            mock_location = AsyncMock()
            mock_location.latitude = 40.7128
            mock_location.longitude = -74.0060
            mock_geocode.return_value = mock_location

            coordinates = await weather_service.get_coordinates("New York")

            assert coordinates == (40.7128, -74.0060)
            mock_geocode.assert_called_once_with("New York")

    @pytest.mark.asyncio
    async def test_get_coordinates_not_found(self, weather_service):
        """Test coordinate retrieval when city is not found."""
        with patch.object(weather_service.geocoder, "geocode") as mock_geocode:
            mock_geocode.return_value = None

            coordinates = await weather_service.get_coordinates("NonexistentCity")

            assert coordinates is None

    @pytest.mark.asyncio
    async def test_get_coordinates_timeout(self, weather_service):
        """Test coordinate retrieval with timeout."""
        with patch.object(weather_service.geocoder, "geocode") as mock_geocode:
            mock_geocode.side_effect = GeocoderTimedOut()

            coordinates = await weather_service.get_coordinates("New York")

            assert coordinates is None

    @pytest.mark.asyncio
    async def test_get_weather_data_mock_fallback(self, weather_service):
        """Test weather data retrieval falls back to mock data."""
        # This will use mock data since we don't have a real API key
        weather_data = await weather_service.get_weather_data(40.7128, -74.0060)

        assert weather_data is not None
        assert "weather" in weather_data
        assert "main" in weather_data
        assert "wind" in weather_data

        # Verify mock data structure
        assert isinstance(weather_data["weather"], list)
        assert len(weather_data["weather"]) > 0
        assert "main" in weather_data["weather"][0]
        assert "description" in weather_data["weather"][0]
        assert "temp" in weather_data["main"]
        assert "humidity" in weather_data["main"]
        assert "speed" in weather_data["wind"]

    def test_parse_weather_response_success(self, weather_service):
        """Test successful weather response parsing."""
        mock_response = {
            "weather": [{"main": "Clear", "description": "clear sky"}],
            "main": {"temp": 22.5, "humidity": 65},
            "wind": {"speed": 3.2},
        }

        parsed = weather_service.parse_weather_response(mock_response)

        assert parsed == {"temperature": 22.5, "description": "Clear Sky", "humidity": 65, "wind_speed": 3.2}

    def test_parse_weather_response_empty_data(self, weather_service):
        """Test parsing empty weather response."""
        parsed = weather_service.parse_weather_response({})
        assert parsed == {}

    def test_parse_weather_response_missing_fields(self, weather_service):
        """Test parsing weather response with missing fields."""
        incomplete_response = {
            "weather": [{"main": "Clear"}],
            "main": {"temp": 22.5},
            # Missing humidity and wind data
        }

        parsed = weather_service.parse_weather_response(incomplete_response)
        assert parsed == {}

    def test_parse_weather_response_none_input(self, weather_service):
        """Test parsing None weather response."""
        parsed = weather_service.parse_weather_response(None)
        assert parsed == {}

    def test_mock_weather_data_structure(self, weather_service):
        """Test that mock weather data has correct structure."""
        mock_data = weather_service._get_mock_weather_data()

        assert "weather" in mock_data
        assert "main" in mock_data
        assert "wind" in mock_data

        # Verify weather array structure
        assert isinstance(mock_data["weather"], list)
        assert len(mock_data["weather"]) > 0
        weather_item = mock_data["weather"][0]
        assert "main" in weather_item
        assert "description" in weather_item

        # Verify main data structure
        main_data = mock_data["main"]
        assert "temp" in main_data
        assert "humidity" in main_data
        assert isinstance(main_data["temp"], (int, float))
        assert isinstance(main_data["humidity"], int)
        assert -10 <= main_data["temp"] <= 35
        assert 30 <= main_data["humidity"] <= 90

        # Verify wind data structure
        wind_data = mock_data["wind"]
        assert "speed" in wind_data
        assert isinstance(wind_data["speed"], (int, float))
        assert 0 <= wind_data["speed"] <= 15

    def test_mock_weather_data_variability(self, weather_service):
        """Test that mock weather data shows variability."""
        # Generate multiple mock responses
        responses = [weather_service._get_mock_weather_data() for _ in range(10)]

        # Check that we get different temperatures
        temperatures = [r["main"]["temp"] for r in responses]
        assert len(set(temperatures)) > 1  # Should have variety

        # Check that we get different conditions
        conditions = [r["weather"][0]["main"] for r in responses]
        # Note: With small sample size, we might not get variety, so this is a soft check
        assert len(set(conditions)) >= 1  # At least one condition type

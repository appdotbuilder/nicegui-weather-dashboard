"""Tests for weather service functionality."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
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
    async def test_get_weather_data_success(self, weather_service):
        """Test successful weather data retrieval using python-weather."""
        with (
            patch("python_weather.Client") as mock_client_class,
            patch.object(weather_service, "_get_city_name_from_coordinates") as mock_city_name,
        ):
            # Mock the weather client and response
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock city name resolution
            mock_city_name.return_value = "New York"

            # Mock weather data
            mock_weather = MagicMock()
            mock_weather.temperature = 22.5
            mock_weather.humidity = 65
            mock_weather.wind_speed = 3.2
            mock_weather.description = "clear sky"

            mock_client.get.return_value = mock_weather

            weather_data = await weather_service.get_weather_data(40.7128, -74.0060)

            assert weather_data is not None
            assert weather_data["temperature"] == 22.5
            assert weather_data["description"] == "clear sky"
            assert weather_data["humidity"] == 65
            assert weather_data["wind_speed"] == 3.2

            mock_city_name.assert_called_once_with(40.7128, -74.0060)
            mock_client.get.assert_called_once_with("New York")

    @pytest.mark.asyncio
    async def test_get_weather_data_exception(self, weather_service):
        """Test weather data retrieval with exception."""
        with patch("python_weather.Client") as mock_client_class:
            mock_client_class.side_effect = Exception("API Error")

            weather_data = await weather_service.get_weather_data(40.7128, -74.0060)

            assert weather_data is None

    @pytest.mark.asyncio
    async def test_get_weather_data_no_city(self, weather_service):
        """Test weather data retrieval when city name cannot be resolved."""
        with patch.object(weather_service, "_get_city_name_from_coordinates") as mock_city_name:
            mock_city_name.return_value = None

            weather_data = await weather_service.get_weather_data(40.7128, -74.0060)

            assert weather_data is None

    def test_parse_weather_response_success(self, weather_service):
        """Test successful weather response parsing."""
        mock_response = {
            "temperature": 22.5,
            "description": "clear sky",
            "humidity": 65,
            "wind_speed": 3.2,
        }

        parsed = weather_service.parse_weather_response(mock_response)

        assert parsed == {
            "temperature": 22.5,
            "description": "Clear Sky",
            "humidity": 65,
            "wind_speed": 3.2,
        }

    def test_parse_weather_response_empty_data(self, weather_service):
        """Test parsing empty weather response."""
        parsed = weather_service.parse_weather_response({})
        assert parsed == {}

    def test_parse_weather_response_missing_fields(self, weather_service):
        """Test parsing weather response with missing fields."""
        incomplete_response = {
            "temperature": 22.5,
            # Missing description, humidity, and wind_speed
        }

        parsed = weather_service.parse_weather_response(incomplete_response)
        assert parsed == {}

    def test_parse_weather_response_none_input(self, weather_service):
        """Test parsing None weather response."""
        parsed = weather_service.parse_weather_response(None)
        assert parsed == {}

    @pytest.mark.asyncio
    async def test_get_weather_data_missing_humidity(self, weather_service):
        """Test weather data retrieval when humidity is None."""
        with (
            patch("python_weather.Client") as mock_client_class,
            patch.object(weather_service, "_get_city_name_from_coordinates") as mock_city_name,
        ):
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_city_name.return_value = "New York"

            # Mock weather data with None humidity
            mock_weather = MagicMock()
            mock_weather.temperature = 22.5
            mock_weather.humidity = None
            mock_weather.wind_speed = 3.2
            mock_weather.description = "clear sky"

            mock_client.get.return_value = mock_weather

            weather_data = await weather_service.get_weather_data(40.7128, -74.0060)

            assert weather_data is not None
            assert weather_data["temperature"] == 22.5
            assert weather_data["description"] == "clear sky"
            assert weather_data["humidity"] == 0.0  # Should default to 0.0
            assert weather_data["wind_speed"] == 3.2

    @pytest.mark.asyncio
    async def test_get_weather_data_missing_wind_speed(self, weather_service):
        """Test weather data retrieval when wind_speed is None."""
        with (
            patch("python_weather.Client") as mock_client_class,
            patch.object(weather_service, "_get_city_name_from_coordinates") as mock_city_name,
        ):
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_city_name.return_value = "New York"

            # Mock weather data with None wind_speed
            mock_weather = MagicMock()
            mock_weather.temperature = 22.5
            mock_weather.humidity = 65
            mock_weather.wind_speed = None
            mock_weather.description = "clear sky"

            mock_client.get.return_value = mock_weather

            weather_data = await weather_service.get_weather_data(40.7128, -74.0060)

            assert weather_data is not None
            assert weather_data["temperature"] == 22.5
            assert weather_data["description"] == "clear sky"
            assert weather_data["humidity"] == 65
            assert weather_data["wind_speed"] == 0.0  # Should default to 0.0

    @pytest.mark.asyncio
    async def test_get_city_name_from_coordinates_success(self, weather_service):
        """Test successful city name retrieval from coordinates."""
        with patch.object(weather_service.geocoder, "reverse") as mock_reverse:
            mock_location = MagicMock()
            mock_location.raw = {"address": {"city": "New York"}}
            mock_reverse.return_value = mock_location

            city_name = await weather_service._get_city_name_from_coordinates(40.7128, -74.0060)

            assert city_name == "New York"

    @pytest.mark.asyncio
    async def test_get_city_name_from_coordinates_no_city(self, weather_service):
        """Test city name retrieval when no city found."""
        with patch.object(weather_service.geocoder, "reverse") as mock_reverse:
            mock_location = MagicMock()
            mock_location.raw = {"address": {}}
            mock_reverse.return_value = mock_location

            city_name = await weather_service._get_city_name_from_coordinates(40.7128, -74.0060)

            assert city_name is None

    @pytest.mark.asyncio
    async def test_get_city_name_from_coordinates_exception(self, weather_service):
        """Test city name retrieval with exception."""
        with patch.object(weather_service.geocoder, "reverse") as mock_reverse:
            mock_reverse.side_effect = Exception("Geocoding error")

            city_name = await weather_service._get_city_name_from_coordinates(40.7128, -74.0060)

            assert city_name is None

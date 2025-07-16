"""Tests for weather app UI functionality."""

import pytest
from unittest.mock import patch
from nicegui.testing import User
from nicegui import ui
from app.models import CityWithWeather
from app.database import reset_db


class TestWeatherApp:
    """Test cases for WeatherApp UI functionality."""

    @pytest.fixture
    def new_db(self):
        """Create fresh database for each test."""
        reset_db()
        yield
        reset_db()

    async def test_main_page_loads(self, user: User, new_db) -> None:
        """Test that the main weather page loads correctly."""
        await user.open("/")

        # Check for main page elements
        await user.should_see("Weather Dashboard")
        await user.should_see("Add New City")
        await user.should_see("No cities added yet")

    async def test_add_city_form_elements(self, user: User, new_db) -> None:
        """Test that the add city form has all required elements."""
        await user.open("/")

        # Check for form elements
        city_inputs = list(user.find(ui.input).elements)
        add_buttons = list(user.find(ui.button).elements)

        # Should have at least 2 inputs (city name and country)
        assert len(city_inputs) >= 2

        # Should have multiple buttons (add, refresh, etc.)
        assert len(add_buttons) >= 2

    async def test_display_city_with_weather(self, user: User, new_db) -> None:
        """Test displaying city with weather data."""
        # Mock city with weather data
        mock_cities = [
            CityWithWeather(
                id=1,
                name="New York",
                country="USA",
                temperature=22.5,
                description="Clear Sky",
                humidity=65,
                wind_speed=3.2,
            )
        ]

        with patch("app.city_service.city_service.get_all_cities_with_weather") as mock_get:
            mock_get.return_value = mock_cities

            await user.open("/")

            # Check city display
            await user.should_see("New York, USA")
            await user.should_see("22.5°C")
            await user.should_see("Clear Sky")

    async def test_display_city_no_weather(self, user: User, new_db) -> None:
        """Test displaying city without weather data."""
        # Mock city without weather data
        mock_cities = [
            CityWithWeather(
                id=1,
                name="Unknown City",
                country="Unknown",
                temperature=None,
                description=None,
                humidity=None,
                wind_speed=None,
            )
        ]

        with patch("app.city_service.city_service.get_all_cities_with_weather") as mock_get:
            mock_get.return_value = mock_cities

            await user.open("/")

            # Check city display with no data
            await user.should_see("Unknown City, Unknown")
            await user.should_see("--°C")

    async def test_multiple_cities_display(self, user: User, new_db) -> None:
        """Test displaying multiple cities."""
        # Mock multiple cities
        mock_cities = [
            CityWithWeather(
                id=1,
                name="New York",
                country="USA",
                temperature=22.5,
                description="Clear Sky",
                humidity=65,
                wind_speed=3.2,
            ),
            CityWithWeather(
                id=2, name="London", country="UK", temperature=15.0, description="Rainy", humidity=80, wind_speed=5.5
            ),
        ]

        with patch("app.city_service.city_service.get_all_cities_with_weather") as mock_get:
            mock_get.return_value = mock_cities

            await user.open("/")

            # Check both cities are displayed
            await user.should_see("New York, USA")
            await user.should_see("22.5°C")
            await user.should_see("London, UK")
            await user.should_see("15.0°C")

    async def test_responsive_layout_elements(self, user: User, new_db) -> None:
        """Test that responsive layout elements are present."""
        await user.open("/")

        # Check for responsive classes and structure
        await user.should_see("Weather Dashboard")

        # Verify form is present
        city_inputs = list(user.find(ui.input).elements)
        assert len(city_inputs) >= 2

        # Verify buttons are present
        buttons = list(user.find(ui.button).elements)
        assert len(buttons) >= 2  # At least add and refresh buttons

    async def test_empty_state_message(self, user: User, new_db) -> None:
        """Test empty state message when no cities are added."""
        with patch("app.city_service.city_service.get_all_cities_with_weather") as mock_get:
            mock_get.return_value = []

            await user.open("/")

            # Check empty state message
            await user.should_see("No cities added yet")
            await user.should_see("Add your first city using the form above")

    async def test_weather_details_display(self, user: User, new_db) -> None:
        """Test that weather details are properly displayed."""
        # Mock city with full weather data
        mock_cities = [
            CityWithWeather(
                id=1,
                name="Paris",
                country="France",
                temperature=18.5,
                description="Partly Cloudy",
                humidity=72,
                wind_speed=4.1,
            )
        ]

        with patch("app.city_service.city_service.get_all_cities_with_weather") as mock_get:
            mock_get.return_value = mock_cities

            await user.open("/")

            # Check detailed weather information
            await user.should_see("Paris, France")
            await user.should_see("18.5°C")
            await user.should_see("Partly Cloudy")
            await user.should_see("💧 72%")  # Humidity
            await user.should_see("💨 4.1 km/h")  # Wind speed

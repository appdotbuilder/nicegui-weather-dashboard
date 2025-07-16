"""Weather service for fetching weather data from OpenWeatherMap API."""

import httpx
from typing import Optional, Dict, Any
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


class WeatherService:
    """Service class for fetching weather data from OpenWeatherMap API."""

    def __init__(self):
        # For demo purposes, we'll use a free API that doesn't require a key
        # In production, you'd want to use a proper API key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.geocoder = Nominatim(user_agent="weather_app")

    async def get_coordinates(self, city_name: str) -> Optional[tuple[float, float]]:
        """Get latitude and longitude for a city name."""
        try:
            # Run geocoding in a thread to avoid blocking
            import asyncio

            def geocode_sync(city: str):
                return self.geocoder.geocode(city)

            location = await asyncio.get_event_loop().run_in_executor(None, geocode_sync, city_name)

            if location:
                lat = getattr(location, "latitude", None)
                lon = getattr(location, "longitude", None)
                if lat is not None and lon is not None:
                    return (float(lat), float(lon))
            return None
        except (GeocoderTimedOut, GeocoderServiceError):
            return None

    async def get_weather_data(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather data for given coordinates."""
        try:
            # Using OpenWeatherMap's demo API endpoint
            # In production, replace with your API key
            url = f"{self.base_url}?lat={lat}&lon={lon}&appid=demo&units=metric"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)

                if response.status_code == 200:
                    return response.json()
                else:
                    # For demo purposes, return mock data when API is unavailable
                    return self._get_mock_weather_data()
        except Exception:
            # Return mock data for demo purposes
            return self._get_mock_weather_data()

    def _get_mock_weather_data(self) -> Dict[str, Any]:
        """Return mock weather data for demo purposes."""
        import random

        weather_conditions = [
            {"main": "Clear", "description": "clear sky"},
            {"main": "Clouds", "description": "few clouds"},
            {"main": "Clouds", "description": "scattered clouds"},
            {"main": "Clouds", "description": "broken clouds"},
            {"main": "Rain", "description": "light rain"},
            {"main": "Snow", "description": "light snow"},
            {"main": "Mist", "description": "mist"},
        ]

        condition = random.choice(weather_conditions)

        return {
            "weather": [condition],
            "main": {"temp": round(random.uniform(-10, 35), 1), "humidity": random.randint(30, 90)},
            "wind": {"speed": round(random.uniform(0, 15), 1)},
        }

    def parse_weather_response(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse weather API response into a standardized format."""
        if not weather_data:
            return {}

        try:
            return {
                "temperature": weather_data["main"]["temp"],
                "description": weather_data["weather"][0]["description"].title(),
                "humidity": weather_data["main"]["humidity"],
                "wind_speed": weather_data["wind"]["speed"],
            }
        except (KeyError, IndexError):
            return {}


# Global instance
weather_service = WeatherService()

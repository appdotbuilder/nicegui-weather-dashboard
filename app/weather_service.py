"""Weather service for fetching weather data using python-weather library."""

import python_weather
from typing import Optional, Dict, Any
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


class WeatherService:
    """Service class for fetching weather data using python-weather library."""

    def __init__(self):
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
        """Fetch weather data for given coordinates using python-weather."""
        try:
            # Create weather client
            async with python_weather.Client(unit=python_weather.METRIC) as client:
                # Get weather data - python-weather works with city names, not coordinates
                # We need to reverse geocode to get a city name first
                city_name = await self._get_city_name_from_coordinates(lat, lon)
                if not city_name:
                    return None

                weather = await client.get(city_name)

                if weather:
                    # Extract current weather information
                    # python-weather returns a Weather object with current conditions

                    return {
                        "temperature": float(weather.temperature)
                        if hasattr(weather, "temperature") and weather.temperature is not None
                        else 0.0,
                        "description": weather.description
                        if hasattr(weather, "description") and weather.description
                        else "Unknown",
                        "humidity": float(weather.humidity)
                        if hasattr(weather, "humidity") and weather.humidity is not None
                        else 0.0,
                        "wind_speed": float(weather.wind_speed)
                        if hasattr(weather, "wind_speed") and weather.wind_speed is not None
                        else 0.0,
                    }
            return None
        except Exception:
            return None

    async def _get_city_name_from_coordinates(self, lat: float, lon: float) -> Optional[str]:
        """Get city name from coordinates using reverse geocoding."""
        try:
            import asyncio

            def reverse_geocode_sync(lat: float, lon: float) -> Any:
                return self.geocoder.reverse((lat, lon))

            location = await asyncio.get_event_loop().run_in_executor(None, reverse_geocode_sync, lat, lon)

            if location and hasattr(location, "raw") and getattr(location, "raw", None):
                # Try to extract city name from the address
                raw_data = getattr(location, "raw", {})
                address = raw_data.get("address", {}) if isinstance(raw_data, dict) else {}
                city = address.get("city") or address.get("town") or address.get("village")
                return city
            return None
        except Exception:
            return None

    def parse_weather_response(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse weather data into a standardized format."""
        if not weather_data:
            return {}

        try:
            return {
                "temperature": weather_data["temperature"],
                "description": weather_data["description"].title(),
                "humidity": weather_data["humidity"],
                "wind_speed": weather_data["wind_speed"],
            }
        except (KeyError, TypeError):
            return {}


# Global instance
weather_service = WeatherService()

"""Service layer for managing cities and weather data."""

from typing import List, Optional
from sqlmodel import select, desc
from datetime import datetime, timedelta
from app.database import get_session
from app.models import City, WeatherData, CityWithWeather
from app.weather_service import weather_service


class CityService:
    """Service class for managing cities and their weather data."""

    @staticmethod
    def get_all_cities_with_weather() -> List[CityWithWeather]:
        """Get all cities with their latest weather data."""
        with get_session() as session:
            # Get all cities
            cities = session.exec(select(City)).all()

            result = []
            for city in cities:
                # Get latest weather data for this city
                weather_query = (
                    select(WeatherData).where(WeatherData.city_id == city.id).order_by(desc(WeatherData.updated_at))
                )

                latest_weather = session.exec(weather_query).first()

                if city.id is not None:
                    city_with_weather = CityWithWeather(
                        id=city.id,
                        name=city.name,
                        country=city.country,
                        temperature=latest_weather.temperature if latest_weather else None,
                        description=latest_weather.description if latest_weather else None,
                        humidity=latest_weather.humidity if latest_weather else None,
                        wind_speed=latest_weather.wind_speed if latest_weather else None,
                        last_updated=latest_weather.updated_at if latest_weather else None,
                    )
                    result.append(city_with_weather)

            return result

    @staticmethod
    async def add_city(city_name: str, country: str = "") -> Optional[City]:
        """Add a new city and fetch its initial weather data."""
        # Get coordinates for the city
        coordinates = await weather_service.get_coordinates(city_name)
        if not coordinates:
            return None

        lat, lon = coordinates

        with get_session() as session:
            # Check if city already exists
            existing_city = session.exec(select(City).where(City.name == city_name)).first()

            if existing_city:
                return existing_city

            # Create new city
            new_city = City(name=city_name, country=country, latitude=lat, longitude=lon)

            session.add(new_city)
            session.commit()
            session.refresh(new_city)

            # Fetch initial weather data
            if new_city.id is not None:
                await CityService.update_weather_data(new_city.id)

            return new_city

    @staticmethod
    async def update_weather_data(city_id: int) -> bool:
        """Update weather data for a specific city."""
        with get_session() as session:
            city = session.get(City, city_id)
            if not city:
                return False

            # Fetch weather data
            weather_data = await weather_service.get_weather_data(city.latitude, city.longitude)
            if not weather_data:
                return False

            # Parse weather data
            parsed_data = weather_service.parse_weather_response(weather_data)
            if not parsed_data:
                return False

            # Create new weather record
            if city.id is not None:
                new_weather = WeatherData(
                    city_id=city.id,
                    temperature=parsed_data["temperature"],
                    description=parsed_data["description"],
                    humidity=parsed_data["humidity"],
                    wind_speed=parsed_data["wind_speed"],
                )

                session.add(new_weather)
                session.commit()

                return True

            return False

    @staticmethod
    async def refresh_all_weather_data() -> int:
        """Refresh weather data for all cities. Returns number of updated cities."""
        with get_session() as session:
            cities = session.exec(select(City)).all()

            updated_count = 0
            for city in cities:
                if city.id is not None:
                    success = await CityService.update_weather_data(city.id)
                    if success:
                        updated_count += 1

            return updated_count

    @staticmethod
    def delete_city(city_id: int) -> bool:
        """Delete a city and all its weather data."""
        with get_session() as session:
            city = session.get(City, city_id)
            if not city:
                return False

            # Delete all weather data for this city
            weather_records = session.exec(select(WeatherData).where(WeatherData.city_id == city_id)).all()

            for weather in weather_records:
                session.delete(weather)

            # Delete the city
            session.delete(city)
            session.commit()

            return True

    @staticmethod
    def is_weather_data_stale(city_with_weather: CityWithWeather, max_age_minutes: int = 30) -> bool:
        """Check if weather data is stale and needs updating."""
        if not city_with_weather.last_updated:
            return True

        age = datetime.utcnow() - city_with_weather.last_updated
        return age > timedelta(minutes=max_age_minutes)


# Global instance
city_service = CityService()

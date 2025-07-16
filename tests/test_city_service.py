"""Tests for city service functionality."""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from app.city_service import CityService
from app.models import City, WeatherData, CityWithWeather
from app.database import reset_db


class TestCityService:
    """Test cases for CityService class."""

    @pytest.fixture
    def new_db(self):
        """Create fresh database for each test."""
        reset_db()
        yield
        reset_db()

    def test_get_all_cities_with_weather_empty(self, new_db):
        """Test getting cities when database is empty."""
        cities = CityService.get_all_cities_with_weather()
        assert cities == []

    def test_get_all_cities_with_weather_no_weather_data(self, new_db):
        """Test getting cities with no weather data."""
        from app.database import get_session

        # Add a city without weather data
        with get_session() as session:
            city = City(name="TestCity", country="TestCountry", latitude=40.7128, longitude=-74.0060)
            session.add(city)
            session.commit()

        cities = CityService.get_all_cities_with_weather()

        assert len(cities) == 1
        city_with_weather = cities[0]
        assert city_with_weather.name == "TestCity"
        assert city_with_weather.country == "TestCountry"
        assert city_with_weather.temperature is None
        assert city_with_weather.description is None
        assert city_with_weather.humidity is None
        assert city_with_weather.wind_speed is None
        assert city_with_weather.last_updated is None

    def test_get_all_cities_with_weather_with_data(self, new_db):
        """Test getting cities with weather data."""
        from app.database import get_session

        # Add city with weather data
        with get_session() as session:
            city = City(name="TestCity", country="TestCountry", latitude=40.7128, longitude=-74.0060)
            session.add(city)
            session.commit()
            session.refresh(city)

            # Add weather data
            if city.id is not None:
                weather = WeatherData(
                    city_id=city.id, temperature=22.5, description="Clear Sky", humidity=65, wind_speed=3.2
                )
                session.add(weather)
                session.commit()

        cities = CityService.get_all_cities_with_weather()

        assert len(cities) == 1
        city_with_weather = cities[0]
        assert city_with_weather.name == "TestCity"
        assert city_with_weather.temperature == 22.5
        assert city_with_weather.description == "Clear Sky"
        assert city_with_weather.humidity == 65
        assert city_with_weather.wind_speed == 3.2
        assert city_with_weather.last_updated is not None

    def test_get_all_cities_with_weather_latest_data(self, new_db):
        """Test that only the latest weather data is returned."""
        from app.database import get_session

        # Add city with multiple weather records
        with get_session() as session:
            city = City(name="TestCity", country="TestCountry", latitude=40.7128, longitude=-74.0060)
            session.add(city)
            session.commit()
            session.refresh(city)

            if city.id is not None:
                # Add older weather data
                old_weather = WeatherData(
                    city_id=city.id,
                    temperature=20.0,
                    description="Old Data",
                    humidity=50,
                    wind_speed=2.0,
                    updated_at=datetime.utcnow() - timedelta(hours=2),
                )
                session.add(old_weather)

                # Add newer weather data
                new_weather = WeatherData(
                    city_id=city.id,
                    temperature=25.0,
                    description="New Data",
                    humidity=70,
                    wind_speed=4.0,
                    updated_at=datetime.utcnow(),
                )
                session.add(new_weather)
                session.commit()

        cities = CityService.get_all_cities_with_weather()

        assert len(cities) == 1
        city_with_weather = cities[0]
        assert city_with_weather.temperature == 25.0
        assert city_with_weather.description == "New Data"

    @pytest.mark.asyncio
    async def test_add_city_success(self, new_db):
        """Test successful city addition."""
        with patch("app.city_service.weather_service.get_coordinates") as mock_coords:
            with patch("app.city_service.CityService.update_weather_data") as mock_update:
                mock_coords.return_value = (40.7128, -74.0060)
                mock_update.return_value = True

                city = await CityService.add_city("New York", "USA")

                assert city is not None
                assert city.name == "New York"
                assert city.country == "USA"
                assert city.latitude == 40.7128
                assert city.longitude == -74.0060
                assert city.id is not None

                mock_coords.assert_called_once_with("New York")
                if city.id is not None:
                    mock_update.assert_called_once_with(city.id)

    @pytest.mark.asyncio
    async def test_add_city_coordinates_not_found(self, new_db):
        """Test adding city when coordinates cannot be found."""
        with patch("app.city_service.weather_service.get_coordinates") as mock_coords:
            mock_coords.return_value = None

            city = await CityService.add_city("NonexistentCity")

            assert city is None

    @pytest.mark.asyncio
    async def test_add_city_duplicate(self, new_db):
        """Test adding duplicate city."""
        with patch("app.city_service.weather_service.get_coordinates") as mock_coords:
            mock_coords.return_value = (40.7128, -74.0060)

            # Add city first time
            city1 = await CityService.add_city("New York", "USA")
            assert city1 is not None

            # Try to add same city again
            city2 = await CityService.add_city("New York", "USA")
            assert city2 is not None
            assert city2.id == city1.id  # Should return existing city

    @pytest.mark.asyncio
    async def test_update_weather_data_success(self, new_db):
        """Test successful weather data update."""
        from app.database import get_session

        # Add a city
        with get_session() as session:
            city = City(name="TestCity", country="TestCountry", latitude=40.7128, longitude=-74.0060)
            session.add(city)
            session.commit()
            session.refresh(city)

            if city.id is not None:
                city_id = city.id

                with patch("app.city_service.weather_service.get_weather_data") as mock_weather:
                    with patch("app.city_service.weather_service.parse_weather_response") as mock_parse:
                        mock_weather.return_value = {"mock": "data"}
                        mock_parse.return_value = {
                            "temperature": 22.5,
                            "description": "Clear Sky",
                            "humidity": 65,
                            "wind_speed": 3.2,
                        }

                        success = await CityService.update_weather_data(city_id)

                        assert success

                        # Verify weather data was stored
                        cities = CityService.get_all_cities_with_weather()
                        assert len(cities) == 1
                        assert cities[0].temperature == 22.5
                        assert cities[0].description == "Clear Sky"

    @pytest.mark.asyncio
    async def test_update_weather_data_city_not_found(self, new_db):
        """Test weather update for non-existent city."""
        success = await CityService.update_weather_data(999)
        assert not success

    @pytest.mark.asyncio
    async def test_update_weather_data_api_failure(self, new_db):
        """Test weather update when API fails."""
        from app.database import get_session

        # Add a city
        with get_session() as session:
            city = City(name="TestCity", country="TestCountry", latitude=40.7128, longitude=-74.0060)
            session.add(city)
            session.commit()
            session.refresh(city)

            if city.id is not None:
                city_id = city.id

                with patch("app.city_service.weather_service.get_weather_data") as mock_weather:
                    mock_weather.return_value = None

                    success = await CityService.update_weather_data(city_id)

                    assert not success

    @pytest.mark.asyncio
    async def test_refresh_all_weather_data(self, new_db):
        """Test refreshing weather data for all cities."""
        from app.database import get_session

        # Add multiple cities
        with get_session() as session:
            city1 = City(name="City1", country="Country1", latitude=40.7128, longitude=-74.0060)
            city2 = City(name="City2", country="Country2", latitude=34.0522, longitude=-118.2437)
            session.add_all([city1, city2])
            session.commit()

        with patch("app.city_service.CityService.update_weather_data") as mock_update:
            mock_update.return_value = True

            updated_count = await CityService.refresh_all_weather_data()

            assert updated_count == 2
            assert mock_update.call_count == 2

    @pytest.mark.asyncio
    async def test_refresh_all_weather_data_some_failures(self, new_db):
        """Test refreshing weather data with some failures."""
        from app.database import get_session

        # Add multiple cities
        with get_session() as session:
            city1 = City(name="City1", country="Country1", latitude=40.7128, longitude=-74.0060)
            city2 = City(name="City2", country="Country2", latitude=34.0522, longitude=-118.2437)
            session.add_all([city1, city2])
            session.commit()

        with patch("app.city_service.CityService.update_weather_data") as mock_update:
            # First city succeeds, second fails
            mock_update.side_effect = [True, False]

            updated_count = await CityService.refresh_all_weather_data()

            assert updated_count == 1
            assert mock_update.call_count == 2

    def test_delete_city_success(self, new_db):
        """Test successful city deletion."""
        from app.database import get_session

        # Add city with weather data
        with get_session() as session:
            city = City(name="TestCity", country="TestCountry", latitude=40.7128, longitude=-74.0060)
            session.add(city)
            session.commit()
            session.refresh(city)

            if city.id is not None:
                weather = WeatherData(
                    city_id=city.id, temperature=22.5, description="Clear Sky", humidity=65, wind_speed=3.2
                )
                session.add(weather)
                session.commit()

                city_id = city.id

                # Delete the city
                success = CityService.delete_city(city_id)
                assert success

                # Verify city and weather data are deleted
                cities = CityService.get_all_cities_with_weather()
                assert len(cities) == 0

    def test_delete_city_not_found(self, new_db):
        """Test deleting non-existent city."""
        success = CityService.delete_city(999)
        assert not success

    def test_is_weather_data_stale_no_data(self):
        """Test stale check with no weather data."""
        city = CityWithWeather(id=1, name="TestCity", country="TestCountry", last_updated=None)

        assert CityService.is_weather_data_stale(city)

    def test_is_weather_data_stale_recent_data(self):
        """Test stale check with recent data."""
        city = CityWithWeather(
            id=1, name="TestCity", country="TestCountry", last_updated=datetime.utcnow() - timedelta(minutes=10)
        )

        assert not CityService.is_weather_data_stale(city, max_age_minutes=30)

    def test_is_weather_data_stale_old_data(self):
        """Test stale check with old data."""
        city = CityWithWeather(
            id=1, name="TestCity", country="TestCountry", last_updated=datetime.utcnow() - timedelta(minutes=45)
        )

        assert CityService.is_weather_data_stale(city, max_age_minutes=30)

    def test_is_weather_data_stale_custom_threshold(self):
        """Test stale check with custom threshold."""
        city = CityWithWeather(
            id=1, name="TestCity", country="TestCountry", last_updated=datetime.utcnow() - timedelta(minutes=10)
        )

        # With 5-minute threshold, 10-minute old data should be stale
        assert CityService.is_weather_data_stale(city, max_age_minutes=5)

        # With 15-minute threshold, 10-minute old data should be fresh
        assert not CityService.is_weather_data_stale(city, max_age_minutes=15)

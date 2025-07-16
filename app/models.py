from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


# Persistent models (stored in database)
class City(SQLModel, table=True):
    __tablename__ = "cities"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    country: str = Field(max_length=100, default="")
    latitude: float = Field()
    longitude: float = Field()
    added_at: datetime = Field(default_factory=datetime.utcnow)


class WeatherData(SQLModel, table=True):
    __tablename__ = "weather_data"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    city_id: int = Field(foreign_key="cities.id", ondelete="CASCADE")
    temperature: float = Field()  # in Celsius
    description: str = Field(max_length=200)
    humidity: int = Field(default=0)  # percentage
    wind_speed: float = Field(default=0.0)  # in km/h
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas (for validation, forms, API requests/responses)
class CityCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    country: str = Field(default="", max_length=100)
    latitude: float = Field()
    longitude: float = Field()


class WeatherDataCreate(SQLModel, table=False):
    city_id: int
    temperature: float
    description: str = Field(max_length=200)
    humidity: int = Field(default=0)
    wind_speed: float = Field(default=0.0)


class WeatherDataUpdate(SQLModel, table=False):
    temperature: Optional[float] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=200)
    humidity: Optional[int] = Field(default=None)
    wind_speed: Optional[float] = Field(default=None)


class CityWithWeather(SQLModel, table=False):
    """Schema for displaying city with current weather information"""

    id: int
    name: str
    country: str
    temperature: Optional[float] = Field(default=None)
    description: Optional[str] = Field(default=None)
    humidity: Optional[int] = Field(default=None)
    wind_speed: Optional[float] = Field(default=None)
    last_updated: Optional[datetime] = Field(default=None)

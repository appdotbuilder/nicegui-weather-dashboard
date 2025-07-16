from app.database import create_tables
from nicegui import app
import app.weather_app


def startup() -> None:
    # this function is called before the first request
    create_tables()
    app.weather_app.create()

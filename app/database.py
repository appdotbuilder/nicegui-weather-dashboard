import os
from sqlmodel import SQLModel, create_engine, Session, text

# Import all models to ensure they're registered. ToDo: replace with specific imports when possible.
from app.models import *  # noqa: F401, F403

DATABASE_URL = os.environ.get("APP_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/postgres")
ENGINE = create_engine(DATABASE_URL, echo=True)


def create_tables():
    SQLModel.metadata.create_all(ENGINE)


def get_session():
    return Session(ENGINE)


def reset_db():
    """Wipe all tables in the database. Use with caution - for testing only!"""
    # Drop in correct order to avoid foreign key issues
    with ENGINE.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS weather_data CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS cities CASCADE"))
        conn.commit()

    SQLModel.metadata.create_all(ENGINE)

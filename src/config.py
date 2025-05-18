from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv


@dataclass
class _Config:
    DB_MAXCON: int
    DB_URL: str  # General connection_pool
    DB_URL_SYNC: str  # For alembic migrations on psycopg2 engine

    SECRET: str

    def init() -> "_Config":
        load_dotenv()

        pg_username, pg_password, pg_database = (
            getenv("PGUSER", "app"),
            getenv("PGPASSWORD", "secret"),
            getenv("PGDATABASE", "appdb"),
        )

        db_url = f"postgresql+asyncpg://{pg_username}:{pg_password}@postgres:5432/{pg_database}"
        db_url_sync = db_url.replace("+asyncpg", "")
        db_maxcon = int(getenv("DB_MAXCON", "10"))

        sec = getenv("SECRET")

        if sec is None:
            raise ValueError("SECRET is not defined in .env file")

        return _Config(
            DB_MAXCON=db_maxcon,
            DB_URL=db_url,
            DB_URL_SYNC=db_url_sync,
            SECRET=sec,
        )


Config = _Config.init()

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "CAMIULA API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/camiula_db"

    # Pool de conexiones — ajustado para equipos de escasos recursos
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 3
    DB_POOL_RECYCLE: int = 1800

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    # Access tokens tienen vida corta — se refrescan con el refresh token.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Auth provider: "local" (dev/testing) o "auth0" (producción)
    AUTH_PROVIDER: str = "local"

    # Auth0 settings (solo cuando AUTH_PROVIDER=auth0)
    AUTH0_DOMAIN: str = ""
    AUTH0_API_AUDIENCE: str = ""
    AUTH0_CLIENT_ID: str = ""
    AUTH0_CLIENT_SECRET: str = ""

    # Caché de permisos — TTL en segundos
    PERMISSION_CACHE_TTL_SECONDS: int = 300

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

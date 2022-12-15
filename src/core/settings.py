"""Settings"""
import base64
import logging
from logging import config as logging_config
from pathlib import Path

from pydantic import BaseModel, BaseSettings, Field

from core.logger import LOGGING

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Superuser(BaseModel):
    username: str
    password: str


class Redis(BaseModel):
    host: str = Field("127.0.0.1")
    port: int = Field(6379)


class Postgres(BaseModel):
    user: str
    password: str
    host: str


class App(BaseModel):
    jwt_secret_key: str
    psw_hash_iterations: int = 1000
    salt_length: int = 20
    kdf_algorithm: str = "p5k2"


class OAuth(BaseModel):
    google_client_id: str
    google_secret: str


class Jaeger(BaseModel):
    host: str = Field("127.0.0.1")
    port: int = Field(6831)


class Settings(BaseSettings):
    redis: Redis
    postgres: Postgres
    app: App
    oauth: OAuth
    superuser: Superuser
    jaeger: Jaeger
    debug: bool = Field(False)

    class Config:
        env_file = BASE_DIR.joinpath(".env")
        env_nested_delimiter = "__"


settings = Settings()


class AppSettings:
    SWAGGER = {"title": "Auth API", "description": "Auth service", "version": "1.0.0"}
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{settings.postgres.user}:{settings.postgres.password}@{settings.postgres.host}/auth"
    )
    REDIS_URL = f"redis://{settings.redis.host}:{settings.redis.port}/0"
    JWT_SECRET_KEY = base64.b64decode(settings.app.jwt_secret_key)
    SECRET_KEY = "192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf"


if settings.debug:
    LOGGING["root"]["level"] = "DEBUG"

logging_config.dictConfig(LOGGING)

logging.debug("%s", settings.dict())

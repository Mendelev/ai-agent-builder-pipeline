# backend/app/core/config.py
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Requirements Manager"
    DEBUG: bool = Field(default=False, description="Debug mode")
    MAX_PAYLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/reqsdb", description="Database connection URL"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # RabbitMQ
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost:5672//", description="RabbitMQ connection URL")

    # Celery
    CELERY_BROKER_URL: str = Field(default="amqp://guest:guest@localhost:5672//", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", description="Celery result backend URL")

    # Security
    SECRET_KEY: str = Field(default="CHANGE_ME_IN_PRODUCTION", description="Secret key for signing")

    # Observability
    ENABLE_TELEMETRY: bool = Field(default=True, description="Enable telemetry")
    LOG_LEVEL: str = Field(default="INFO", description="Log level")


settings = Settings()

# backend/app/core/config.py
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Requirements Manager"
    DEBUG: bool = Field(default=False, env="DEBUG")
    MAX_PAYLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/reqsdb",
        env="DATABASE_URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # RabbitMQ
    RABBITMQ_URL: str = Field(
        default="amqp://guest:guest@localhost:5672//",
        env="RABBITMQ_URL"
    )
    
    # Celery
    CELERY_BROKER_URL: str = Field(
        default="amqp://guest:guest@localhost:5672//",
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_RESULT_BACKEND"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        env="SECRET_KEY"
    )
    
    # Observability
    ENABLE_TELEMETRY: bool = Field(default=True, env="ENABLE_TELEMETRY")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)
    
    # Application
    APP_NAME: str = "AI Agent Builder Pipeline"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_agent_builder"
    
    # Celery / Redis
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    
    # Feature Flags
    DEV_ALLOW_PARTIAL_OBS: bool = False  # Relaxes warnings, NOT security
    
    # Git Repository Settings
    MAX_REPO_SIZE_MB: int = 100
    GIT_CLONE_TIMEOUT: int = 300  # 5 minutes
    SANDBOX_BASE_PATH: str = "/tmp/repos"
    
    # Encryption Settings
    MASTER_ENCRYPTION_KEY: Optional[str] = None  # Base64 encoded key
    KMS_KEY_ID: Optional[str] = None  # For production KMS integration
    
    # Celery Settings
    CELERY_CONCURRENCY: int = 4
    CELERY_MAX_RETRIES: int = 3
    
    def get_origins_list(self) -> List[str]:
        """Convert ALLOWED_ORIGINS string to list"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()

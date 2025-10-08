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
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    
    # Feature Flags
    DEV_ALLOW_PARTIAL_OBS: bool = False  # Relaxes warnings, NOT security
    
    def get_origins_list(self) -> List[str]:
        """Convert ALLOWED_ORIGINS string to list"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()

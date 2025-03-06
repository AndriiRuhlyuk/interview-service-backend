import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Назва додатку
    APP_NAME: str = "Interview Service"
    APP_VERSION: str = "1.0.0"
    
    # База даних
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "interview_service")
    
    # PeopleForce API
    PEOPLEFORCE_API_URL: str = os.getenv("PEOPLEFORCE_API_URL", "https://api.peopleforce.io")
    PEOPLEFORCE_API_KEY: Optional[str] = os.getenv("PEOPLEFORCE_API_KEY")

    # JWT Secret для автентифікації
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()

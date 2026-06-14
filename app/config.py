import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 Hours
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sql_app.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    BASE_URL: str = os.getenv("BASE_URL", "http://127.0.0.1:8000")

    class Config:
        env_file = ".env"

settings = Settings()
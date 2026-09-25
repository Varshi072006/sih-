from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'challenge_to_impact.db'}"
    JWT_SECRET: str = "dev-only-change-me"
    JWT_EXPIRE_MINUTES: int = 480
    JWT_REFRESH_EXPIRE_MINUTES: int = 10080
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    DEMO_MODE: bool = True
    MAX_UPLOAD_MB: int = 25
    ALGORITHM: str = "HS256"


settings = Settings()

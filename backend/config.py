import secrets
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_KEY: str = "change-me-please"
    DATABASE_URL: str = "sqlite+aiosqlite:///./firewall_monitor.db"
    ALERT_TIMEOUT_MINUTES: int = 5
    SMTP_HOSTNAME: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "user@example.com"
    SMTP_PASSWORD: str = "password"
    ALERT_RECIPIENT_EMAIL: str = "admin@example.com"
    ALERT_SENDER_EMAIL: str = "alerts@example.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

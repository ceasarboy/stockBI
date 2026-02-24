from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "MacroQuant"
    PROJECT_VERSION: str = "1.0.0"
    
    DATABASE_URL: str = "postgresql+asyncpg://macroquant:macroquant123@localhost:5432/macroquant"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    WEBHOOK_TOKEN: str = "your_secure_webhook_token"
    
    YFINANCE_ENABLED: bool = True
    AKSHARE_ENABLED: bool = True
    
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    SERVERCHAN_KEY: Optional[str] = None
    WECHAT_WEBHOOK_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

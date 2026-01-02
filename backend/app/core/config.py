from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    APP_NAME: str = "Violence Monitoring System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./violence_monitoring.db"
    
    # Security
    JWT_SECRET: str = "super-secret-key-please-change"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    UPLOAD_DIR: str = "data/uploads"
    MODELS_DIR: str = "models"
    
    # Alerts (Optional)
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    GMAIL_REFRESH_TOKEN: Optional[str] = None
    GMAIL_SENDER: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # Local Model Server
    LOCAL_MODEL_API_URL: str = "http://localhost:1234/v1" 
    LOCAL_MODEL_NAME: str = "moondream-2b-2025-04-14"
    
    # Paths
    EVIDENCE_DIR: str = "Evidence"
    
    # Langflow (Keeping for legacy if needed, but primary is now Gemini)

    class Config:
        env_file = ".env"

settings = Settings()
